# PRD – Versión en Español

## 1. Objetivo
Construir un **agente financiero con IA** que funcione a través de **Telegram**. El agente debe permitir registrar **ingresos, gastos, transferencias y conversiones** en lenguaje natural. Debe soportar **cuentas multi-moneda** (ej. Belo con USDT y ARS) y brindar **saldos, reportes y análisis** en tiempo real.

---

## 2. Alcance (MVP)

### Funcionalidades principales
1. **Registro de transacciones en lenguaje natural**
   - Ejemplos:
     - “Cobré 6k USD de sueldo en Deel.”
     - “Transferí 1k USD a Astropay y recibí 992 USD.”
     - “Gasté 400k ARS en Galicia.”
     - “Convertí 10 USDT a ARS a 1350.”
   - Extrae: tipo, monto, cuenta origen/destino, moneda, fecha, cotización (si falta, buscar en tiempo real).

2. **Gestión de cuentas**
   - Si una cuenta no existe, se crea automáticamente.
   - Cada cuenta puede manejar **múltiples monedas**.
   - Los saldos se actualizan automáticamente con cada transacción.

3. **Cotización de monedas**
   - Integración con APIs para USD ↔ ARS (oficial, blue, MEP), stablecoins y cripto.
   - Si falta cotización, buscar en tiempo real.

4. **Consultas y balances**
   - Ejemplos:
     - “¿Cuánto gasté en agosto?”
     - “Qué saldo tengo en Galicia?”
     - “Mostrame todas mis cuentas.”
   - Respuesta:
     ```
     * Deel – USD 6,000
     * Astropay – USD 992
     * Galicia – ARS 400,000
     * Belo – USDT 50, ARS 13,500
     * Efectivo – ARS 50,000
     ```

5. **Reportes mensuales**
   - Generados automáticamente al cierre de cada mes.
   - Incluyen: ingresos totales, gastos totales, ahorro neto, saldos por cuenta, transacción más grande.

---

## 3. Fuera de Alcance (MVP)
- Dashboard web.
- Multiusuario.
- Categorización avanzada de gastos.
- Recomendaciones de inversión.

---

## 4. Tecnologías

- **Orquestación del agente**: LangChain (Python) + OpenAI API.
- **Interfaz**: Telegram Bot API.
- **Base de datos**: PostgreSQL con SQLAlchemy.

### Esquema de base de datos
- `accounts` → id, nombre, tipo, created_at.
- `account_balances` → id, account_id (FK), moneda, saldo.
- `transactions` → id, tipo, monto, moneda, account_from_id, account_to_id, moneda_destino, monto_destino, cotización, descripción, fecha.

---

## 5. Diseño del agente
- **Agente ReAct de LangChain** con Tools:
  - **DB Tool** → registrar y consultar transacciones/saldos.
  - **FX Tool** → obtener cotizaciones.

Ejemplo de flujo:
```
Usuario: "Convertí 10 USDT a ARS en Belo a 1350"
Agente:
  - Detecta conversión
  - Actualiza Belo: -10 USDT, +13,500 ARS
  - Registra transacción
Respuesta: "Conversión registrada en Belo: -10 USDT → +13,500 ARS"
```

---

## 6. UX (Telegram)
- Mensajes naturales para registrar transacciones.
- Comandos:
  - `/balance` → todas las cuentas.
  - `/balance <cuenta>` → una sola cuenta.
  - `/report` → reporte mensual.
  - `/help` → guía de uso.

---

## 7. Roadmap

**MVP**
- Parsing de transacciones.
- Cuentas multi-moneda.
- Consultas y reportes en Telegram.

**Fase 2**
- Categorización (comida, transporte, etc.).
- Consolidación de patrimonio neto (convertir todo a moneda base).
- Dashboard web.
- Multiusuario.
- Agente asesor de gastos e inversiones.

---

## 8. Métricas de éxito
- >90% de transacciones clasificadas correctamente.
- Creación automática de cuentas sin errores.
- Consistencia de saldos entre consultas y transacciones.
- Respuesta < 5s por consulta.