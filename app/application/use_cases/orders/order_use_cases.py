from decimal import Decimal
from app.domain.entities.order import Order, OrderItem
from app.domain.repositories.order_repository import OrderRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.repositories.product_repository import ProductRepository
from app.domain.repositories.vehicle_repository import VehicleRepository
from app.application.dto.order_dto import (
    CreateOrderRequest,
    UpdateOrderRequest,
    OrderResponse,
    OrderItemResponse,
)
from app.shared.exceptions.custom_exceptions import (
    NotFoundException,
    BusinessRuleException,
    InsufficientStockException,
    ForbiddenException,
)
from app.shared.constants.roles import UserRole, OrderStatus
from app.shared.utils.weight_converter import weight_summary
from app.application.dto.product_dto import StockWeightResponse

# Solo EN_PROCESO ocupa capacidad del vehículo.
# PENDIENTE: stock ya descontado pero el vehículo aún no está cargado.
_ESTADOS_ACTIVOS = [OrderStatus.EN_PROCESO]


def _build_item_response(item: OrderItem) -> OrderItemResponse:
    return OrderItemResponse(
        id=item.id,
        producto_id=item.producto_id,
        cantidad_kg=item.cantidad_kg,
        cantidad=StockWeightResponse(**weight_summary(item.cantidad_kg)),
        precio_unitario_kg=item.precio_unitario_kg,
        precio_compra_unitario_kg=item.precio_compra_unitario_kg,
        subtotal=item.cantidad_kg * item.precio_unitario_kg,
    )


def _build_response(order: Order) -> OrderResponse:
    items = [_build_item_response(i) for i in order.items]
    total_kg = sum(float(i.cantidad_kg) for i in order.items)
    return OrderResponse(
        id=order.id,
        nombre_cliente=order.nombre_cliente,
        documento_cliente=order.documento_cliente,
        id_domiciliario=order.id_domiciliario,
        nombre_domiciliario=order.nombre_domiciliario,
        id_vehiculo=order.id_vehiculo,
        lugar=order.lugar,
        fecha_hora=order.fecha_hora,
        precio_total=order.precio_total,
        estado=order.estado,
        items=items,
        total_kg=total_kg,
        total=StockWeightResponse(**weight_summary(total_kg)),
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


class CreateOrderUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,
        user_repo: UserRepository,
        product_repo: ProductRepository,
        vehicle_repo: VehicleRepository,
    ):
        self.order_repo = order_repo
        self.user_repo = user_repo
        self.product_repo = product_repo
        self.vehicle_repo = vehicle_repo

    def execute(self, request: CreateOrderRequest, created_by: int) -> OrderResponse:
        # Validar domiciliario
        driver = self.user_repo.get_by_id(request.id_domiciliario)
        if not driver or not driver.is_active:
            raise NotFoundException("Repartidor o Administrador", request.id_domiciliario)
        role_val = driver.role.value if hasattr(driver.role, "value") else str(driver.role)
        driver_role = role_val.split(".")[-1].lower()
        if driver_role not in ["repartidor", "admin"]:
            raise BusinessRuleException(f"El usuario '{driver.nombre}' tiene un rol no válido: '{driver_role}'")

        # Validar vehículo (OBLIGATORIO)
        vehicle = self.vehicle_repo.get_by_id(request.id_vehiculo)
        if not vehicle or not vehicle.activo:
            raise NotFoundException("Vehículo activo", request.id_vehiculo)

        # Construir items
        order_items: list[OrderItem] = []
        precio_total_calculado = Decimal("0.00")
        total_kg = Decimal("0")

        estado_inicial = OrderStatus.PENDIENTE

        # Acumula cuánto se ha solicitado de cada producto EN ESTE MISMO pedido,
        # para detectar sobregiro cuando el mismo producto aparece en varias líneas.
        kg_solicitado_por_producto: dict[int, Decimal] = {}

        for item_req in request.items:
            product = self.product_repo.get_by_id(item_req.id_producto)
            if not product or not product.activo:
                raise NotFoundException("Producto activo", item_req.id_producto)
            # Los envíos son siempre salidas (ventas al cliente), así que
            # se valida el stock disponible SIEMPRE al momento de crear,
            # aunque el estado inicial sea PENDIENTE.
            ya_solicitado = kg_solicitado_por_producto.get(product.id, Decimal("0"))
            total_acumulado = ya_solicitado + item_req.cantidad_kg
            if not product.has_sufficient_stock(total_acumulado):
                raise InsufficientStockException(
                    product.nombre, float(product.stock_kg), float(total_acumulado)
                )
            kg_solicitado_por_producto[product.id] = total_acumulado
            subtotal_item = item_req.cantidad_kg * product.precio
            precio_total_calculado += subtotal_item
            total_kg += item_req.cantidad_kg
            order_items.append(
                OrderItem(
                    id=0,
                    pedido_id=0,
                    producto_id=product.id,
                    cantidad_kg=item_req.cantidad_kg,
                    precio_unitario_kg=product.precio,
                    precio_compra_unitario_kg=product.precio_compra_kg,  # snapshot
                )
            )

        # La capacidad del vehículo NO se valida al crear (PENDIENTE no ocupa carga).
        # La validación ocurre cuando el repartidor pase el pedido a EN_PROCESO.

        order = Order(
            id=0,
            nombre_cliente=request.nombre_cliente,
            documento_cliente=request.documento_cliente,
            id_domiciliario=request.id_domiciliario,
            nombre_domiciliario=driver.nombre,  # snapshot
            id_vehiculo=request.id_vehiculo,
            lugar=request.lugar,
            fecha_hora=request.fecha_hora,
            precio_total=precio_total_calculado,
            estado=estado_inicial,
            items=order_items,
            created_by=created_by,
            updated_by=created_by,
        )
        created = self.order_repo.create(order)

        # Los envíos son salidas: descontar stock al crear (queda reservado desde PENDIENTE)
        for item_req in request.items:
            product = self.product_repo.get_by_id(item_req.id_producto)
            if product:
                self.product_repo.update_stock(
                    product.id, product.stock_kg - item_req.cantidad_kg, created_by
                )

        # La capacidad del vehículo NO se descuenta al crear (PENDIENTE).
        # Se descuenta cuando el repartidor pase el pedido a EN_PROCESO.

        return _build_response(created)


class GetOrderUseCase:
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    def execute(self, order_id: int, requester_id: int, requester_role: str) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundException("Pedido", order_id)
        if requester_role == UserRole.REPARTIDOR and order.id_domiciliario != requester_id:
            raise ForbiddenException("Solo puedes ver los pedidos que te están asignados.")
        if requester_role == UserRole.EMPLEADO and order.created_by != requester_id:
            raise ForbiddenException("Solo puedes ver los pedidos que tú creaste.")
        return _build_response(order)


class ListOrdersUseCase:
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    def execute(
        self,
        page: int = 1,
        page_size: int = 20,
        id_domiciliario: int | None = None,
        estado: OrderStatus | None = None,
        search: str | None = None,
        requester_id: int | None = None,
        requester_role: str | None = None,
    ) -> tuple[list[OrderResponse], int]:
        if requester_role == UserRole.REPARTIDOR:
            id_domiciliario = requester_id
        orders, total = self.order_repo.list(
            page=page,
            page_size=page_size,
            id_domiciliario=id_domiciliario,
            estado=estado,
            search=search,
        )
        return [_build_response(o) for o in orders], total


class UpdateOrderUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,
        user_repo: UserRepository,
        product_repo: ProductRepository,
        vehicle_repo: VehicleRepository,
    ):
        self.order_repo = order_repo
        self.user_repo = user_repo
        self.product_repo = product_repo
        self.vehicle_repo = vehicle_repo

    def execute(
        self,
        order_id: int,
        request: UpdateOrderRequest,
        updated_by: int,
        updater_role: str,
    ) -> OrderResponse:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundException("Pedido", order_id)

        if updater_role == UserRole.REPARTIDOR and order.id_domiciliario != updated_by:
            raise ForbiddenException("Solo puedes modificar los pedidos que te están asignados.")

        # Los envíos reservan stock desde PENDIENTE (al crearse).
        # Stock se libera SOLO al ENTREGADO (ya no vuelve) o CANCELADO (se devuelve).
        estados_con_stock_reservado = [OrderStatus.PENDIENTE, OrderStatus.EN_PROCESO]
        estados_finales = [OrderStatus.ENTREGADO, OrderStatus.CANCELADO]

        estado_anterior = order.estado
        estado_nuevo = request.estado if request.estado is not None else estado_anterior
        items_cambiaron = request.items is not None

        # Si los items cambian mientras el pedido tiene stock reservado,
        # devolver el stock anterior para re-validar con los nuevos items.
        if items_cambiaron and estado_anterior in estados_con_stock_reservado:
            for old_item in order.items:
                product = self.product_repo.get_by_id(old_item.producto_id)
                if product:
                    self.product_repo.update_stock(
                        product.id, product.stock_kg + old_item.cantidad_kg, updated_by
                    )

        # --- Actualizar campos básicos
        if request.nombre_cliente is not None: order.nombre_cliente = request.nombre_cliente
        if request.documento_cliente is not None: order.documento_cliente = request.documento_cliente
        if request.lugar is not None: order.lugar = request.lugar
        if request.fecha_hora is not None: order.fecha_hora = request.fecha_hora
        if request.estado is not None: order.estado = request.estado

        if request.id_domiciliario is not None:
            driver = self.user_repo.get_by_id(request.id_domiciliario)
            if not driver or not driver.is_active:
                raise NotFoundException("Repartidor o Administrador", request.id_domiciliario)
            role_val = driver.role.value if hasattr(driver.role, "value") else str(driver.role)
            driver_role = role_val.split(".")[-1].lower()
            if driver_role not in ["repartidor", "admin"]:
                raise BusinessRuleException(f"El usuario '{driver.nombre}' tiene un rol no válido.")
            order.id_domiciliario = request.id_domiciliario

        # --- Cambio de vehículo
        if request.id_vehiculo is not None and request.id_vehiculo != order.id_vehiculo:
            new_vehicle = self.vehicle_repo.get_by_id(request.id_vehiculo)
            if not new_vehicle or not new_vehicle.activo:
                raise NotFoundException("Vehículo activo", request.id_vehiculo)
            total_kg = order.total_kg
            # Solo mover carga si el pedido ya está EN_PROCESO (PENDIENTE no ocupa carga)
            if estado_anterior == OrderStatus.EN_PROCESO and order.id_vehiculo:
                old_vehicle = self.vehicle_repo.get_by_id(order.id_vehiculo)
                if old_vehicle:
                    self.vehicle_repo.update_carga(
                        old_vehicle.id,
                        max(Decimal("0"), old_vehicle.carga_actual_kg - total_kg),
                        updated_by
                    )
                if not new_vehicle.tiene_capacidad(total_kg):
                    raise BusinessRuleException(
                        f"El vehículo '{new_vehicle.placa}' no tiene capacidad suficiente. "
                        f"Disponible: {float(new_vehicle.capacidad_disponible_kg):.2f} kg, "
                        f"Solicitado: {float(total_kg):.2f} kg."
                    )
                self.vehicle_repo.update_carga(
                    new_vehicle.id,
                    new_vehicle.carga_actual_kg + total_kg,
                    updated_by
                )
            order.id_vehiculo = request.id_vehiculo

        # --- Reconstruir items si cambiaron
        if items_cambiaron:
            new_items: list[OrderItem] = []
            nuevo_precio_total = Decimal("0.00")
            nuevo_estado_requiere_stock = estado_nuevo in estados_con_stock_reservado
            kg_solicitado_por_producto: dict[int, Decimal] = {}
            for item_req in request.items:
                product = self.product_repo.get_by_id(item_req.id_producto)
                if not product or not product.activo:
                    raise NotFoundException("Producto activo", item_req.id_producto)
                # Validar stock si el pedido seguirá activo (reserva stock),
                # acumulando por producto para detectar duplicados en el mismo pedido
                ya_solicitado = kg_solicitado_por_producto.get(product.id, Decimal("0"))
                total_acumulado = ya_solicitado + item_req.cantidad_kg
                if nuevo_estado_requiere_stock and not product.has_sufficient_stock(total_acumulado):
                    raise InsufficientStockException(
                        product.nombre, float(product.stock_kg), float(total_acumulado)
                    )
                kg_solicitado_por_producto[product.id] = total_acumulado
                subtotal_item = item_req.cantidad_kg * product.precio
                nuevo_precio_total += subtotal_item
                new_items.append(
                    OrderItem(
                        id=0,
                        pedido_id=order_id,
                        producto_id=product.id,
                        cantidad_kg=item_req.cantidad_kg,
                        precio_unitario_kg=product.precio,
                        precio_compra_unitario_kg=product.precio_compra_kg,  # snapshot
                    )
                )
            order.items = new_items
            order.precio_total = nuevo_precio_total

            # Re-descontar stock con los nuevos items si el pedido sigue activo
            if nuevo_estado_requiere_stock:
                for item in order.items:
                    product = self.product_repo.get_by_id(item.producto_id)
                    if product:
                        self.product_repo.update_stock(
                            product.id, product.stock_kg - item.cantidad_kg, updated_by
                        )

        # Si el estado pasa de activo a final, gestionar stock de productos
        if estado_anterior in estados_con_stock_reservado and estado_nuevo in estados_finales:
            if estado_nuevo == OrderStatus.CANCELADO:
                # Cancelado: devolver el stock reservado
                for item in order.items:
                    product = self.product_repo.get_by_id(item.producto_id)
                    if product:
                        self.product_repo.update_stock(
                            product.id, product.stock_kg + item.cantidad_kg, updated_by
                        )
            # ENTREGADO: el stock ya fue descontado al crear, no se hace nada más

        # --- Lógica de capacidad del vehículo por cambio de estado
        # Regla: solo EN_PROCESO ocupa capacidad.
        #   PENDIENTE → EN_PROCESO : descontar capacidad (el repartidor toma el pedido)
        #   EN_PROCESO → ENTREGADO : liberar capacidad (pedido entregado)
        #   EN_PROCESO → CANCELADO : liberar capacidad (pedido cancelado en ruta)
        #   PENDIENTE  → CANCELADO : no hay capacidad que liberar
        if order.id_vehiculo:
            vehicle = self.vehicle_repo.get_by_id(order.id_vehiculo)
            if vehicle:
                total_kg = order.total_kg

                # Tomar el pedido: PENDIENTE → EN_PROCESO
                if estado_anterior == OrderStatus.PENDIENTE and estado_nuevo == OrderStatus.EN_PROCESO:
                    if not vehicle.tiene_capacidad(total_kg):
                        raise BusinessRuleException(
                            f"El vehículo '{vehicle.placa}' no tiene capacidad suficiente para cargar este pedido. "
                            f"Disponible: {float(vehicle.capacidad_disponible_kg):.2f} kg, "
                            f"Solicitado: {float(total_kg):.2f} kg."
                        )
                    self.vehicle_repo.update_carga(
                        vehicle.id,
                        vehicle.carga_actual_kg + total_kg,
                        updated_by,
                    )

                # Terminar el pedido: EN_PROCESO → ENTREGADO o CANCELADO
                elif estado_anterior == OrderStatus.EN_PROCESO and estado_nuevo in [OrderStatus.ENTREGADO, OrderStatus.CANCELADO]:
                    nueva_carga = max(Decimal("0"), vehicle.carga_actual_kg - total_kg)
                    self.vehicle_repo.update_carga(vehicle.id, nueva_carga, updated_by)

        order.updated_by = updated_by
        updated = self.order_repo.update(order)
        return _build_response(updated)


class DeleteOrderUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,
        product_repo: ProductRepository,
        vehicle_repo: VehicleRepository,
    ):
        self.order_repo = order_repo
        self.product_repo = product_repo
        self.vehicle_repo = vehicle_repo

    def execute(self, order_id: int, deleted_by: int, deleter_role: str) -> None:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundException("Pedido", order_id)

        if deleter_role == UserRole.EMPLEADO and order.created_by != deleted_by:
            raise ForbiddenException("Solo puedes cancelar los pedidos que tú creaste.")

        if not order.is_cancellable and deleter_role != UserRole.ADMIN:
            raise BusinessRuleException(
                f"No se puede cancelar un pedido en estado '{order.estado}'."
            )

        # El stock se reserva desde PENDIENTE al crear el envío.
        # Al cancelar/eliminar un pedido activo (PENDIENTE o EN_PROCESO), se devuelve el stock.
        # Si ya está ENTREGADO no se devuelve (la entrega ya se realizó).
        if order.estado in [OrderStatus.PENDIENTE, OrderStatus.EN_PROCESO]:
            for item in order.items:
                product = self.product_repo.get_by_id(item.producto_id)
                if product:
                    self.product_repo.update_stock(
                        product.id, product.stock_kg + item.cantidad_kg, deleted_by
                    )

        # Liberar capacidad del vehículo si el pedido estaba activo
        if order.estado in _ESTADOS_ACTIVOS and order.id_vehiculo:
            vehicle = self.vehicle_repo.get_by_id(order.id_vehiculo)
            if vehicle:
                total_kg = order.total_kg
                nueva_carga = max(Decimal("0"), vehicle.carga_actual_kg - total_kg)
                self.vehicle_repo.update_carga(vehicle.id, nueva_carga, deleted_by)

        self.order_repo.soft_delete(order_id, deleted_by)
