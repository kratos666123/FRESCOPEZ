from decimal import Decimal
from app.domain.entities.delivery import Delivery, DeliveryItem
from app.domain.repositories.delivery_repository import DeliveryRepository
from app.domain.repositories.product_repository import ProductRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.repositories.vehicle_repository import VehicleRepository
from app.application.dto.delivery_dto import (
    CreateDeliveryRequest,
    UpdateDeliveryRequest,
    DeliveryResponse,
    DeliveryItemResponse,
)
from app.shared.exceptions.custom_exceptions import (
    NotFoundException,
    ForbiddenException,
    BusinessRuleException,
    InsufficientStockException,
)
from app.shared.constants.roles import DeliveryType, DeliveryStatus, UserRole
from app.shared.utils.weight_converter import weight_summary
from app.application.dto.product_dto import StockWeightResponse


def _build_item_response(item: DeliveryItem) -> DeliveryItemResponse:
    return DeliveryItemResponse(
        id=item.id,
        producto_id=item.producto_id,
        cantidad_kg=item.cantidad_kg,
        cantidad=StockWeightResponse(**weight_summary(item.cantidad_kg)),
        precio_compra_unitario_kg=item.precio_compra_unitario_kg,
    )


def _build_response(delivery: Delivery) -> DeliveryResponse:
    items = [_build_item_response(i) for i in delivery.items]
    total_kg = sum(float(i.cantidad_kg) for i in delivery.items)
    return DeliveryResponse(
        id=delivery.id,
        tipo=delivery.tipo,
        estado=delivery.estado,
        fecha_hora=delivery.fecha_hora,
        id_domiciliario=delivery.id_domiciliario,
        nombre_domiciliario=delivery.nombre_domiciliario,
        id_vehiculo=delivery.id_vehiculo,
        observaciones=delivery.observaciones,
        items=items,
        total_kg=total_kg,
        total=StockWeightResponse(**weight_summary(total_kg)),
        created_at=delivery.created_at,
        updated_at=delivery.updated_at,
    )


# Las entregas son siempre COMPRA: stock aumenta al COMPLETAR, se revierte al CANCELAR-desde-COMPLETADA
_ESTADOS_TERMINADOS = [DeliveryStatus.COMPLETADA, DeliveryStatus.CANCELADA]
# Solo EN_PROCESO ocupa capacidad del vehículo.
# PENDIENTE: entrega registrada pero el vehículo aún no está cargado.
_ESTADOS_ACTIVOS = [DeliveryStatus.EN_PROCESO]


class CreateDeliveryUseCase:
    """
    Las Entregas son SIEMPRE de tipo COMPRA (empresa recibe mercancía del proveedor).
    El stock de los productos aumenta SOLO al marcar la entrega como COMPLETADA.
    Mientras está PENDIENTE NO ocupa capacidad del vehículo ni mueve stock.
    Al pasar a EN_PROCESO ocupa capacidad. Al COMPLETAR suma stock.
    Vehículo OBLIGATORIO con capacidad suficiente.
    Solo Admin y Empleado pueden CREAR; Repartidor solo actualiza estado.
    """

    def __init__(
        self,
        delivery_repo: DeliveryRepository,
        product_repo: ProductRepository,
        user_repo: UserRepository,
        vehicle_repo: VehicleRepository,
    ):
        self.delivery_repo = delivery_repo
        self.product_repo = product_repo
        self.user_repo = user_repo
        self.vehicle_repo = vehicle_repo

    def execute(self, request: CreateDeliveryRequest, created_by: int, creator_role: str) -> DeliveryResponse:
        # Solo Admin y Empleado pueden crear
        if creator_role == UserRole.REPARTIDOR:
            raise ForbiddenException("Los repartidores no pueden crear entregas. Solo pueden actualizar su estado.")

        # Validar domiciliario
        driver = self.user_repo.get_by_id(request.id_domiciliario)
        if not driver or not driver.is_active:
            raise NotFoundException("Repartidor o Administrador", request.id_domiciliario)
        role_val = driver.role.value if hasattr(driver.role, "value") else str(driver.role)
        driver_role = role_val.split(".")[-1].lower()
        if driver_role not in ["repartidor", "admin"]:
            raise BusinessRuleException(f"El usuario '{driver.nombre}' no puede ser asignado como repartidor.")

        # Validar vehículo (OBLIGATORIO)
        vehicle = self.vehicle_repo.get_by_id(request.id_vehiculo)
        if not vehicle or not vehicle.activo:
            raise NotFoundException("Vehículo activo", request.id_vehiculo)

        # Construir items (solo compra, sin validación de stock saliente)
        delivery_items: list[DeliveryItem] = []
        total_kg = Decimal("0")
        for item_req in request.items:
            product = self.product_repo.get_by_id(item_req.id_producto)
            if not product or not product.activo:
                raise NotFoundException("Producto activo", item_req.id_producto)
            delivery_items.append(
                DeliveryItem(
                    id=0,
                    entrega_id=0,
                    producto_id=product.id,
                    cantidad_kg=item_req.cantidad_kg,
                    precio_compra_unitario_kg=product.precio_compra_kg,  # snapshot al momento
                )
            )
            total_kg += item_req.cantidad_kg

        # La capacidad NO se valida ni descuenta al crear (PENDIENTE no ocupa carga).
        # Se valida y descuenta cuando el repartidor pase a EN_PROCESO.

        delivery = Delivery(
            id=0,
            tipo=DeliveryType.COMPRA,   # Siempre compra
            estado=DeliveryStatus.PENDIENTE,
            fecha_hora=request.fecha_hora,
            id_domiciliario=request.id_domiciliario,
            nombre_domiciliario=driver.nombre,  # snapshot
            id_vehiculo=request.id_vehiculo,
            observaciones=request.observaciones,
            items=delivery_items,
            created_by=created_by,
            updated_by=created_by,
        )
        created = self.delivery_repo.create(delivery)

        # La carga del vehículo se registra al pasar a EN_PROCESO, no aquí.

        return _build_response(created)


class GetDeliveryUseCase:
    def __init__(self, delivery_repo: DeliveryRepository):
        self.delivery_repo = delivery_repo

    def execute(self, delivery_id: int, requester_id: int, requester_role: str) -> DeliveryResponse:
        delivery = self.delivery_repo.get_by_id(delivery_id)
        if not delivery:
            raise NotFoundException("Entrega", delivery_id)

        # Repartidor solo ve las que tiene asignadas
        if requester_role == UserRole.REPARTIDOR and delivery.id_domiciliario != requester_id:
            raise ForbiddenException("Solo puedes ver las entregas que te están asignadas.")
        # Empleado ve todas (misma lógica que envíos)
        return _build_response(delivery)


class ListDeliveriesUseCase:
    def __init__(self, delivery_repo: DeliveryRepository):
        self.delivery_repo = delivery_repo

    def execute(
        self,
        page: int = 1,
        page_size: int = 20,
        tipo: DeliveryType | None = None,
        estado: DeliveryStatus | None = None,
        search: str | None = None,
        requester_id: int | None = None,
        requester_role: str | None = None,
    ) -> tuple[list[DeliveryResponse], int]:
        id_domiciliario_filter = None

        # Repartidor: solo ve las que tiene asignadas
        if requester_role == UserRole.REPARTIDOR:
            id_domiciliario_filter = requester_id

        deliveries, total = self.delivery_repo.list(
            page=page,
            page_size=page_size,
            tipo=tipo,
            estado=estado,
            id_domiciliario=id_domiciliario_filter,
            search=search,
        )
        return [_build_response(d) for d in deliveries], total


class UpdateDeliveryUseCase:
    """
    Repartidor: SOLO puede cambiar estado (en_proceso -> completada / cancelada).
    Admin/Empleado: pueden editar todo.

    Lógica de stock (igual que envíos):
      COMPRA completada -> aumenta stock. Cancelada-desde-COMPLETADA -> revierte.
      
    Lógica de capacidad vehículo:
      Estado ACTIVO (pendiente/en_proceso) -> ocupa capacidad
      Estado COMPLETADA/CANCELADA -> libera capacidad del vehículo
    """

    def __init__(
        self,
        delivery_repo: DeliveryRepository,
        product_repo: ProductRepository,
        user_repo: UserRepository,
        vehicle_repo: VehicleRepository,
    ):
        self.delivery_repo = delivery_repo
        self.product_repo = product_repo
        self.user_repo = user_repo
        self.vehicle_repo = vehicle_repo

    def execute(
        self,
        delivery_id: int,
        request: UpdateDeliveryRequest,
        updated_by: int,
        updater_role: str,
    ) -> DeliveryResponse:
        delivery = self.delivery_repo.get_by_id(delivery_id)
        if not delivery:
            raise NotFoundException("Entrega", delivery_id)

        estado_anterior = delivery.estado
        estado_nuevo = request.estado if request.estado is not None else estado_anterior

        # Repartidor: solo puede cambiar estado, y solo en las que tiene asignadas
        if updater_role == UserRole.REPARTIDOR:
            if delivery.id_domiciliario != updated_by:
                raise ForbiddenException("Solo puedes modificar las entregas que te están asignadas.")
            # Repartidor solo puede cambiar estado; no puede modificar otros campos
            allowed_estados = [DeliveryStatus.EN_PROCESO, DeliveryStatus.COMPLETADA, DeliveryStatus.CANCELADA]
            if request.estado is not None and request.estado not in allowed_estados:
                raise BusinessRuleException("Los repartidores solo pueden actualizar el estado de la entrega.")
            # Forzamos que solo se aplique el cambio de estado
            delivery.estado = estado_nuevo
            delivery.updated_by = updated_by
            # Si el estado nuevo termina la entrega, aplicar lógica de stock/capacidad
            self._aplicar_logica_estado(delivery, estado_anterior, estado_nuevo, updated_by)
            updated = self.delivery_repo.update(delivery)
            return _build_response(updated)

        # Admin/Empleado: pueden editar todo
        # Validar domiciliario si cambia
        if request.id_domiciliario is not None:
            driver = self.user_repo.get_by_id(request.id_domiciliario)
            if not driver or not driver.is_active:
                raise NotFoundException("Repartidor o Administrador", request.id_domiciliario)
            role_val = driver.role.value if hasattr(driver.role, "value") else str(driver.role)
            driver_role = role_val.split(".")[-1].lower()
            if driver_role not in ["repartidor", "admin"]:
                raise BusinessRuleException(f"El usuario '{driver.nombre}' no puede ser asignado como repartidor.")
            delivery.id_domiciliario = request.id_domiciliario

        # Validar vehículo si cambia
        if request.id_vehiculo is not None and request.id_vehiculo != delivery.id_vehiculo:
            new_vehicle = self.vehicle_repo.get_by_id(request.id_vehiculo)
            if not new_vehicle or not new_vehicle.activo:
                raise NotFoundException("Vehículo activo", request.id_vehiculo)

            total_kg = delivery.total_kg
            # Solo mover carga si la entrega ya está EN_PROCESO (PENDIENTE no ocupa carga)
            if estado_anterior == DeliveryStatus.EN_PROCESO and delivery.id_vehiculo:
                old_vehicle = self.vehicle_repo.get_by_id(delivery.id_vehiculo)
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
            delivery.id_vehiculo = request.id_vehiculo

        # tipo siempre es COMPRA, no se modifica
        if request.fecha_hora is not None:
            delivery.fecha_hora = request.fecha_hora
        if request.observaciones is not None:
            delivery.observaciones = request.observaciones

        # Si cambian items (solo admin/empleado)
        if request.items is not None:
            # Calcular nuevo total_kg para validar capacidad vehículo
            nuevo_total_kg = sum(item_req.cantidad_kg for item_req in request.items)
            vehiculo_id = delivery.id_vehiculo
            # Solo ajustar carga del vehículo si la entrega está EN_PROCESO
            if vehiculo_id and estado_nuevo == DeliveryStatus.EN_PROCESO:
                vehicle = self.vehicle_repo.get_by_id(vehiculo_id)
                if vehicle:
                    cap_disponible_real = vehicle.capacidad_disponible_kg + delivery.total_kg
                    if nuevo_total_kg > cap_disponible_real:
                        raise BusinessRuleException(
                            f"El vehículo '{vehicle.placa}' no tiene capacidad para los nuevos items. "
                            f"Disponible real: {float(cap_disponible_real):.2f} kg, "
                            f"Solicitado: {float(nuevo_total_kg):.2f} kg."
                        )
                    self.vehicle_repo.update_carga(
                        vehicle.id,
                        vehicle.carga_actual_kg - delivery.total_kg + nuevo_total_kg,
                        updated_by
                    )

            new_items: list[DeliveryItem] = []
            for item_req in request.items:
                product = self.product_repo.get_by_id(item_req.id_producto)
                if not product or not product.activo:
                    raise NotFoundException("Producto activo", item_req.id_producto)
                new_items.append(
                    DeliveryItem(
                        id=0,
                        entrega_id=delivery_id,
                        producto_id=product.id,
                        cantidad_kg=item_req.cantidad_kg,
                        precio_compra_unitario_kg=product.precio_compra_kg,
                    )
                )
            delivery.items = new_items

        delivery.estado = estado_nuevo
        delivery.updated_by = updated_by

        # Aplicar lógica de stock y capacidad según transición de estado
        self._aplicar_logica_estado(delivery, estado_anterior, estado_nuevo, updated_by)

        updated = self.delivery_repo.update(delivery)
        return _build_response(updated)

    def _aplicar_logica_estado(
        self,
        delivery: Delivery,
        estado_anterior: DeliveryStatus,
        estado_nuevo: DeliveryStatus,
        updated_by: int,
    ):
        """
        Lógica de stock e inventario según la transición de estado.
        Las entregas son SIEMPRE compra (llegada de mercancía):
          - COMPLETADA: aumenta el stock de los productos.
          - CANCELADA desde COMPLETADA: revierte el aumento (quita el stock que se había sumado).
          - CANCELADA desde PENDIENTE/EN_PROCESO: no hay stock que revertir.
        """
        if estado_anterior == estado_nuevo:
            return

        # --- LÓGICA DE STOCK (solo COMPRA) ---
        # Al COMPLETAR: sumar stock a los productos
        if estado_nuevo == DeliveryStatus.COMPLETADA and estado_anterior != DeliveryStatus.COMPLETADA:
            for item in delivery.items:
                product = self.product_repo.get_by_id(item.producto_id)
                if product:
                    new_stock = product.stock_kg + item.cantidad_kg
                    self.product_repo.update_stock(product.id, new_stock, updated_by)

        # Al CANCELAR desde COMPLETADA: revertir la suma de stock
        if estado_nuevo == DeliveryStatus.CANCELADA and estado_anterior == DeliveryStatus.COMPLETADA:
            for item in delivery.items:
                product = self.product_repo.get_by_id(item.producto_id)
                if product:
                    new_stock = max(Decimal("0"), product.stock_kg - item.cantidad_kg)
                    self.product_repo.update_stock(product.id, new_stock, updated_by)

        # --- LÓGICA DE CAPACIDAD DEL VEHÍCULO ---
        # PENDIENTE → EN_PROCESO : el repartidor toma la entrega, descontar capacidad
        if estado_anterior == DeliveryStatus.PENDIENTE and estado_nuevo == DeliveryStatus.EN_PROCESO:
            if delivery.id_vehiculo:
                vehicle = self.vehicle_repo.get_by_id(delivery.id_vehiculo)
                if vehicle:
                    total_kg = delivery.total_kg
                    if not vehicle.tiene_capacidad(total_kg):
                        raise BusinessRuleException(
                            f"El vehículo '{vehicle.placa}' no tiene capacidad suficiente para cargar esta entrega. "
                            f"Disponible: {float(vehicle.capacidad_disponible_kg):.2f} kg, "
                            f"Solicitado: {float(total_kg):.2f} kg."
                        )
                    self.vehicle_repo.update_carga(
                        vehicle.id, vehicle.carga_actual_kg + total_kg, updated_by
                    )

        # EN_PROCESO → COMPLETADA o CANCELADA : liberar capacidad
        elif estado_anterior == DeliveryStatus.EN_PROCESO and estado_nuevo in _ESTADOS_TERMINADOS:
            if delivery.id_vehiculo:
                vehicle = self.vehicle_repo.get_by_id(delivery.id_vehiculo)
                if vehicle:
                    total_kg = delivery.total_kg
                    nueva_carga = max(Decimal("0"), vehicle.carga_actual_kg - total_kg)
                    self.vehicle_repo.update_carga(vehicle.id, nueva_carga, updated_by)


class DeleteDeliveryUseCase:
    def __init__(self, delivery_repo: DeliveryRepository, vehicle_repo: VehicleRepository):
        self.delivery_repo = delivery_repo
        self.vehicle_repo = vehicle_repo

    def execute(self, delivery_id: int, deleted_by: int, deleter_role: str) -> None:
        delivery = self.delivery_repo.get_by_id(delivery_id)
        if not delivery:
            raise NotFoundException("Entrega", delivery_id)

        if deleter_role not in [UserRole.ADMIN]:
            raise ForbiddenException("Solo el administrador puede eliminar entregas.")

        # Si la entrega estaba activa, liberar capacidad del vehículo
        if delivery.estado in _ESTADOS_ACTIVOS and delivery.id_vehiculo:
            vehicle = self.vehicle_repo.get_by_id(delivery.id_vehiculo)
            if vehicle:
                total_kg = delivery.total_kg
                nueva_carga = max(Decimal("0"), vehicle.carga_actual_kg - total_kg)
                self.vehicle_repo.update_carga(vehicle.id, nueva_carga, deleted_by)

        self.delivery_repo.soft_delete(delivery_id, deleted_by)
