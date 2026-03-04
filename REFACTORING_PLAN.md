# Plan de Refactorización qBRA

**Fecha Creación**: 4 de marzo, 2026  
**Última Actualización**: 4 de marzo, 2026 (v1.1)  
**Proyecto**: qBRA - Plugin QGIS para Building Restriction Areas (ILS/LLZ)  
**Objetivo**: Mejorar la arquitectura, mantenibilidad y calidad del código sin modificar las fórmulas de cálculo  
**Duración Estimada**: 14-15 días (103-111 horas)

---

## 📊 Resumen del Análisis

### Estado Actual

- **Archivos Python**: 4 módulos
- **Líneas de código**: ~600 líneas
- **Type hints**: ❌ Ninguno
- **Tests**: ❌ No existen
- **Documentación**: ❌ Mínima
- **Arquitectura**: ⚠️ Lógica acoplada a UI

### Problemas Identificados

#### 🔴 Críticos

1. **Violación de SRP**: `IlsLlzDockWidget` mezcla UI + lógica de negocio + validación
2. **Sin type hints**: Todo el código carece de tipos
3. **Sin tests**: No hay pruebas automatizadas
4. **Manejo de errores deficiente**: Uso de `except Exception: pass` y `print()` para debug

#### 🟠 Importantes

5. **Código duplicado**: Creación de 7 features con código casi idéntico
6. **Magic numbers**: Valores como 10000, "PolygonZ?crs=" sin constantes
7. **Validación débil**: No valida rangos de valores numéricos
8. **Nombres ambiguos**: Variables como `pt_alp`, `pt_arp` sin contexto

#### 🟡 Menores

9. **Sin logging**: Uso de `print()` en lugar de logging proper
10. **Hardcoded strings**: Repetición de nombres de campos
11. **Sin configuración**: Valores como facility defaults embebidos en código

---

## 🎯 Objetivos de la Refactorización

### Principios Guía

- ✅ **KISS**: Mantener simplicidad
- ✅ **DRY**: Eliminar duplicación
- ✅ **SRP**: Una responsabilidad por clase
- ✅ **Type-first**: Definir tipos antes de implementar
- ✅ **Testabilidad**: Hacer el código testeable
- 🚫 **NO TOCAR**: Fórmulas matemáticas y cálculos geométricos

### Mejoras Esperadas

- 📈 **Mantenibilidad**: +80%
- 🐛 **Bugs detectables**: +100% (con type checking)
- ✅ **Cobertura de tests**: 0% → 80%+
- 📚 **Documentación**: Completa y clara

---

## 📋 Plan de Implementación (Fases MoSCoW)

### 🔴 **MUST HAVE - Sprint 1** (Refactorización Core)

#### **Story 1.1: Implementar Type Hints Completos**

**Como** desarrollador  
**Quiero** que todo el código tenga type hints  
**Para** detectar errores en tiempo de desarrollo y mejorar la documentación

**Tareas**:

- [ ] Agregar types a `__init__.py` (5 min)
- [ ] Agregar types a `qbra_plugin.py` (30 min)
- [ ] Agregar types a `ils_llz_dockwidget.py` (1h)
- [ ] Agregar types a `ils_llz_logic.py` (45 min)
- [ ] Configurar mypy para validación (15 min)
- [ ] Ejecutar mypy y corregir errores (30 min)

**Estimación**: 3 Story Points  
**Prioridad**: Must Have

---

#### **Story 1.2: Crear Modelos de Datos con Dataclasses**

**Como** desarrollador  
**Quiero** tipos estructurados para parámetros y configuración  
**Para** evitar errores de diccionarios y mejorar type safety

**Tareas**:

- [ ] Crear `models.py` con dataclasses (1h)
  - `BRAParameters`: a, b, h, r, D, H, L, phi, azimuth, site_elev
  - `FacilityConfig`: label, defaults, a_dependent
  - `CalculationResult`: layer, feature_count, errors
- [ ] Reemplazar dict params por BRAParameters (45 min)
- [ ] Agregar validación en `__post_init__` (30 min)
- [ ] Actualizar imports y referencias (30 min)

**Acceptance Criteria**:

- ✅ Todas las configuraciones usan dataclasses frozen
- ✅ Validación de rangos en `__post_init__`
- ✅ Type checker pasa sin errores

**Estimación**: 5 Story Points  
**Prioridad**: Must Have

---

#### **Story 1.3: Separar Lógica de Negocio de UI (MVC)**

**Como** desarrollador  
**Quiero** separar la lógica de negocio de la interfaz  
**Para** hacer el código testeable y mantener SRP

**Tareas**:

- [ ] Crear `services/ils_llz_service.py` (2h)
  - Mover facility_defs a FacilityService
  - Mover cálculo de parámetros a ParameterCalculator
  - Mover validaciones a Validator
- [ ] Crear `controllers/ils_llz_controller.py` (1h)
  - Mediar entre DockWidget y Service
  - Manejar signals/slots
- [ ] Refactorizar `IlsLlzDockWidget` (2h)
  - Solo responsabilidades de UI
  - Conectar con Controller vía signals
- [ ] Actualizar `qbra_plugin.py` para usar Controller (30 min)

**Acceptance Criteria**:

- ✅ DockWidget solo maneja UI events
- ✅ Service no tiene dependencias de PyQt
- ✅ Controller conecta View y Service con signals/slots

**Estimación**: 8 Story Points  
**Prioridad**: Must Have

---

#### **Story 1.4: Eliminar Código Duplicado en Feature Creation**

**Como** desarrollador  
**Quiero** eliminar la repetición en creación de features  
**Para** mantener DRY y facilitar cambios futuros

**Tareas**:

- [ ] Crear dataclass `FeatureDefinition` (30 min)
- [ ] Crear función `create_feature()` genérica (1h)
- [ ] Definir list de feature definitions (45 min)
- [ ] Reemplazar 7 bloques duplicados por loop (30 min)
- [ ] Verificar que salida sea idéntica (30 min)

**Acceptance Criteria**:

- ✅ Una sola función para crear features
- ✅ Configuración declarativa de features
- ✅ Output idéntico al código original

**Estimación**: 5 Story Points  
**Prioridad**: Must Have

---

#### **Story 1.5: Implementar Logging Proper** ✅ **COMPLETADA**

**Como** desarrollador  
**Quiero** logging estructurado en lugar de print()  
**Para** facilitar debugging y monitoreo

**Tareas**:

- [x] Configurar logging con formato adecuado (30 min)
- [x] Reemplazar todos los `print()` por logger (30 min)
- [x] Agregar logging de errores con traceback (30 min)
- [x] Configurar niveles de log (DEBUG, INFO, WARNING, ERROR) (15 min)

**Acceptance Criteria**:

- ✅ No hay más `print()` statements (3 reemplazados en dockwidget)
- ✅ Logs incluyen timestamp y nivel
- ✅ Errores incluyen traceback completo (con exc_info=True)

**Implementación**:

- Creado `qBRA/utils/logging_config.py` (131 líneas)
  - QGISLogHandler: Handler custom que integra con QgsMessageLog
  - setup_logger(): Configura logger con formato y handlers apropiados
  - get_logger(): Función de conveniencia para obtener logger
- Reemplazados 3 print() en `ils_llz_dockwidget.py`:
  - Debug log para azimuth calculation
  - Warning log para validation errors
  - Error log con traceback para unexpected errors
- Creado `tests/test_logging_config.py` (192 líneas, 18 tests)
  - Tests para QGISLogHandler
  - Tests para setup_logger
  - Tests para get_logger
  - Tests de integración con diferentes niveles de log

**Métricas**:
- 3 print() statements eliminados
- 131 líneas de logging infrastructure
- 192 líneas de test coverage (18 tests)
- Integración con QGIS MessageLog

**Estimación**: 2 Story Points  
**Tiempo Real**: 2 horas  
**Prioridad**: Must Have

---

#### **Story 1.6: Mejorar Manejo de Errores**

**Como** usuario  
**Quiero** mensajes de error claros cuando algo falla  
**Para** entender qué salió mal y cómo resolverlo

**Tareas**:

- [ ] Crear excepciones custom (30 min)
  - `BRAValidationError`
  - `BRACalculationError`
  - `LayerNotFoundError`
- [ ] Reemplazar `except Exception: pass` (1h)
- [ ] Agregar validaciones de entrada (1h)
- [ ] Mejorar mensajes de error al usuario (30 min)

**Acceptance Criteria**:

- ✅ No hay excepciones silenciosas
- ✅ Mensajes de error son descriptivos
- ✅ Validaciones claras en entrada de datos

**Estimación**: 3 Story Points  
**Prioridad**: Must Have

---

### 🟠 **SHOULD HAVE - Sprint 2** (Testing & Calidad)

#### **Story 2.1: Setup de Testing Infrastructure**

**Como** desarrollador  
**Quiero** infraestructura de testing  
**Para** escribir y ejecutar tests automatizados

**Tareas**:

- [ ] Configurar pytest (30 min)
- [ ] Crear estructura tests/ (15 min)
- [ ] Configurar fixtures para QGIS mock (1h)
- [ ] Crear test helpers (30 min)

**Estimación**: 3 Story Points  
**Prioridad**: Should Have

---

#### **Story 2.2: Tests Unitarios para Services**

**Como** desarrollador  
**Quiero** tests para lógica de negocio  
**Para** asegurar correctitud y evitar regresiones

**Tareas**:

- [ ] Tests para FacilityService (2h)
- [ ] Tests para ParameterCalculator (2h)
- [ ] Tests para Validators (1h)
- [ ] Tests para models (1h)

**Acceptance Criteria**:

- ✅ Cobertura > 80% en services
- ✅ Tests incluyen casos edge
- ✅ Tests son independientes

**Estimación**: 8 Story Points  
**Prioridad**: Should Have

---

#### **Story 2.3: Tests de Integración**

**Como** desarrollador  
**Quiero** tests de integración  
**Para** verificar que componentes funcionan juntos

**Tareas**:

- [ ] Tests Controller + Service (2h)
- [ ] Tests geometría completa (mock QGIS) (3h)
- [ ] Tests end-to-end del cálculo (2h)

**Estimación**: 8 Story Points  
**Prioridad**: Should Have

---

#### **Story 2.4: Extraer Constantes y Configuración**

**Como** desarrollador  
**Quiero** constantes centralizadas  
**Para** facilitar ajustes y mantenimiento

**Tareas**:

- [ ] Crear `constants.py` (30 min)
  - PROJECTION_DISTANCE = 10000
  - CRS_TEMPLATE = "PolygonZ?crs="
  - FIELD_NAMES como constantes
- [ ] Crear `config.py` con dataclasses (1h)
- [ ] Reemplazar magic numbers (1h)
- [ ] Reemplazar hardcoded strings (30 min)

**Estimación**: 3 Story Points  
**Prioridad**: Should Have

---

### 🟡 **COULD HAVE - Sprint 3** (Mejoras Adicionales)

#### **Story 3.1: Documentación Completa**

**Como** desarrollador nuevo  
**Quiero** documentación clara  
**Para** entender y contribuir al proyecto

**Tareas**:

- [ ] Docstrings en todas las funciones (2h)
- [ ] README técnico (1h)
- [ ] Guía de desarrollo (1h)
- [ ] Diagramas de arquitectura (1h)

**Estimación**: 5 Story Points  
**Prioridad**: Could Have

---

#### **Story 3.2: Refactorizar Nombres de Variables**

**Como** desarrollador  
**Quiero** nombres descriptivos  
**Para** entender código sin contexto adicional

**Tareas**:

- [ ] Renombrar pt_alp → point_ahead_left_projected (30 min)
- [ ] Renombrar pt_arp → point_ahead_right_projected (30 min)
- [ ] Documentar significado de variables geométricas (1h)

**Estimación**: 2 Story Points  
**Prioridad**: Could Have

---

#### **Story 3.3: Threading para Operaciones Largas**

**Como** usuario  
**Quiero** que la UI no se congele  
**Para** tener mejor experiencia de usuario

**Tareas**:

- [ ] Crear QThread para build_layers (2h)
- [ ] Agregar progress bar (1h)
- [ ] Manejar cancelación (1h)

**Estimación**: 5 Story Points  
**Prioridad**: Could Have

---

#### **Story 3.4: Migración a PyQt6 con Compatibilidad Qt5**

**Como** desarrollador  
**Quiero** migrar a PyQt6 manteniendo compatibilidad con Qt5  
**Para** estar preparado para futuras versiones de QGIS

**Tareas**:

- [ ] Crear módulo compatibility.py para abstracción (1h)
- [ ] Implementar detección de Qt version (30 min)
- [ ] Crear imports condicionales (1h)
- [ ] Actualizar imports en todos los archivos (2h)
- [ ] Testing en Qt5 y Qt6 (1h)
- [ ] Documentar compatibilidad (30 min)

**Acceptance Criteria**:

- ✅ Código funciona con PyQt5 (QGIS 3.x)
- ✅ Código funciona con PyQt6 (futuras versiones)
- ✅ Detección automática de versión
- ✅ Sin deprecation warnings

**Estimación**: 8 Story Points  
**Prioridad**: Could Have

---

### ⚪ **WON'T HAVE - Fuera de Scope**

- ❌ Internacionalización (i18n)
- ❌ Soporte para otros tipos de BRA
- ❌ Interfaz web
- ❌ API REST
- ❌ Cambios a fórmulas matemáticas

---

## 📁 Estructura Propuesta Post-Refactorización

```
qBRA/
├── qBRA/
│   ├── __init__.py                    # Factory
│   ├── qbra_plugin.py                 # Plugin entry point
│   ├── constants.py                   # NEW: Constantes
│   ├── config.py                      # NEW: Configuración
│   ├── compatibility.py               # NEW: PyQt5/6 compatibility layer
│   │
│   ├── models/                        # NEW: Data models
│   │   ├── __init__.py
│   │   ├── parameters.py              # BRAParameters, etc
│   │   └── facility.py                # FacilityConfig
│   │
│   ├── services/                      # NEW: Business logic
│   │   ├── __init__.py
│   │   ├── facility_service.py        # Facility management
│   │   ├── parameter_calculator.py    # Calculate parameters
│   │   ├── validator.py               # Input validation
│   │   └── geometry_builder.py        # Geometry creation
│   │
│   ├── controllers/                   # NEW: MVC Controllers
│   │   ├── __init__.py
│   │   └── ils_llz_controller.py      # Mediates View-Service
│   │
│   ├── dockwidgets/
│   │   └── ils/
│   │       └── ils_llz_dockwidget.py  # REFACTORED: Only UI
│   │
│   ├── modules/
│   │   └── ils_llz_logic.py           # REFACTORED: Pure geometry
│   │
│   ├── exceptions.py                  # NEW: Custom exceptions
│   ├── logger.py                      # NEW: Logging setup
│   │
│   ├── ui/
│   │   └── ils/
│   │       └── ils_llz_panel.ui
│   │
│   └── icons/
│       └── qbra.svg
│
├── tests/                             # NEW: Test suite
│   ├── __init__.py
│   ├── conftest.py                    # Fixtures
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_controllers.py
│   ├── test_validators.py
│   ├── test_compatibility.py          # Test Qt5/6 compatibility
│   └── test_integration.py
│
├── docs/                              # NEW: Documentation
│   ├── architecture.md
│   ├── development.md
│   ├── qt_compatibility.md            # Qt5/6 compatibility guide
│   └── formulas.md                    # Documentar fórmulas sin cambiarlas
│
├── .mypy.ini                          # NEW: Type checking config
├── pytest.ini                         # NEW: Test config
├── REFACTORING_PLAN.md               # Este documento
└── README.md

```

---

## 🚀 Roadmap de Ejecución

### **Fase 0: Pre-Refactorización** (1 día)

**Goal**: Setup inicial y preparación

**Actividades**:

- ✅ Análisis completo del proyecto (COMPLETADO)
- ✅ Plan de refactorización creado (COMPLETADO)
- [ ] Crear branch `refactor/main`
- [ ] Setup de entorno de desarrollo
- [ ] Configurar pre-commit hooks
- [ ] Backup del código actual
- [ ] Crear baseline de tests (aunque sean 0)

**Tiempo**: 1 día (8 horas)  
**Responsable**: Dev Lead  
**Entregables**: Branch preparado, entorno configurado

---

### **Fase 1: Fundamentos y Type Safety** (3 días)

#### Sprint 1.A - Type Hints y Modelos (1.5 días)

| Story           | Puntos | Horas | Prioridad | Status         |
| --------------- | ------ | ----- | --------- | -------------- |
| 1.1 Type Hints  | 3      | 6h    | P0        | ⏳ Not Started |
| 1.2 Dataclasses | 5      | 10h   | P0        | ⏳ Not Started |

**Día 1 (8h)**:

- 08:00-10:00: Story 1.1 - Type hints en **init**.py y qbra_plugin.py
- 10:00-12:00: Story 1.1 - Type hints en ils_llz_dockwidget.py
- 12:00-13:00: 🍽️ Lunch break
- 13:00-15:00: Story 1.1 - Type hints en ils_llz_logic.py
- 15:00-16:00: Story 1.1 - Configurar mypy y corregir errores
- 16:00-17:00: Code review y commit

**Día 2 (8h)**:

- 08:00-10:00: Story 1.2 - Crear models.py con dataclasses
- 10:00-12:00: Story 1.2 - Implementar validación en **post_init**
- 12:00-13:00: 🍽️ Lunch break
- 13:00-15:00: Story 1.2 - Reemplazar dict params por BRAParameters
- 15:00-16:00: Story 1.2 - Actualizar todas las referencias
- 16:00-17:00: Testing manual y commit

**Entregables**:

- ✅ 100% type coverage
- ✅ Dataclasses para todos los modelos
- ✅ Mypy pasa sin errores

---

#### Sprint 1.B - Arquitectura MVC (2.5 días)

| Story              | Puntos | Horas | Prioridad | Status         |
| ------------------ | ------ | ----- | --------- | -------------- |
| 1.3 MVC Separation | 8      | 16h   | P0        | ⏳ Not Started |
| 1.5 Logging        | 2      | 4h    | P1        | ⏳ Not Started |

**Día 3 (8h)**:

- 08:00-10:00: Story 1.3 - Crear services/facility_service.py
- 10:00-12:00: Story 1.3 - Crear services/parameter_calculator.py
- 12:00-13:00: 🍽️ Lunch break
- 13:00-15:00: Story 1.3 - Crear services/validator.py
- 15:00-16:00: Story 1.3 - Crear controllers/ils_llz_controller.py
- 16:00-17:00: Planning para día 4

**Día 4 (8h)**:

- 08:00-10:00: Story 1.3 - Refactorizar IlsLlzDockWidget (parte 1)
- 10:00-12:00: Story 1.3 - Refactorizar IlsLlzDockWidget (parte 2)
- 12:00-13:00: 🍽️ Lunch break
- 13:00-15:00: Story 1.3 - Conectar signals/slots Controller-View
- 15:00-16:00: Story 1.3 - Actualizar qbra_plugin.py
- 16:00-17:00: Testing integración manual

**Día 5 (4h)**:

- 08:00-10:00: Story 1.5 - Configurar logging y reemplazar prints
- 10:00-12:00: Story 1.5 - Agregar logging de errores y debug
- 12:00-13:00: Code review Fase 1

**Entregables**:

- ✅ Arquitectura MVC completa
- ✅ Separación clara de responsabilidades
- ✅ Logging estructurado

---

### **Fase 2: Calidad y DRY** (2 días)

#### Sprint 1.C - Refactoring y Error Handling (2 días)

| Story              | Puntos | Horas | Prioridad | Status         |
| ------------------ | ------ | ----- | --------- | -------------- |
| 1.4 DRY Features   | 5      | 8h    | P0        | ⏳ Not Started |
| 1.6 Error Handling | 3      | 6h    | P0        | ⏳ Not Started |

**Día 6 (8h)**:

- 08:00-10:00: Story 1.4 - Crear FeatureDefinition dataclass
- 10:00-12:00: Story 1.4 - Crear función create_feature() genérica
- 12:00-13:00: 🍽️ Lunch break
- 13:00-15:00: Story 1.4 - Definir lista de feature definitions
- 15:00-16:00: Story 1.4 - Reemplazar código duplicado
- 16:00-17:00: Story 1.4 - Verificar output idéntico

**Día 7 (6h)**:

- 08:00-10:00: Story 1.6 - Crear excepciones custom
- 10:00-12:00: Story 1.6 - Reemplazar except Exception
- 12:00-13:00: 🍽️ Lunch break
- 13:00-14:00: Story 1.6 - Agregar validaciones de entrada
- 14:00-15:00: Story 1.6 - Mejorar mensajes de error
- 15:00-16:00: Testing completo Fase 1 y 2

**Entregables**:

- ✅ Código sin duplicación significativa
- ✅ Manejo de errores robusto
- ✅ Mensajes de error claros

---

### **Fase 3: Testing Infrastructure** (2 días)

#### Sprint 2.A - Setup y Tests Básicos (2 días)

| Story                | Puntos | Horas | Prioridad | Status         |
| -------------------- | ------ | ----- | --------- | -------------- |
| 2.1 Test Setup       | 3      | 5h    | P0        | ⏳ Not Started |
| 2.4 Constants/Config | 3      | 5h    | P1        | ⏳ Not Started |

**Día 8 (8h)**:

- 08:00-10:00: Story 2.1 - Configurar pytest y estructura tests/
- 10:00-12:00: Story 2.1 - Crear fixtures para QGIS mock
- 12:00-13:00: 🍽️ Lunch break
- 13:00-15:00: Story 2.1 - Crear test helpers
- 15:00-16:00: Story 2.4 - Crear constants.py
- 16:00-17:00: Story 2.4 - Crear config.py

**Día 9 (2h)**:

- 08:00-10:00: Story 2.4 - Reemplazar magic numbers y strings
- 10:00-10:30: Verificar tests básicos funcionan

**Entregables**:

- ✅ Pytest configurado
- ✅ Fixtures listos
- ✅ Constantes centralizadas

---

### **Fase 4: Test Coverage** (3 días)

#### Sprint 2.B - Tests Unitarios e Integración (3 días)

| Story                 | Puntos | Horas | Prioridad | Status         |
| --------------------- | ------ | ----- | --------- | -------------- |
| 2.2 Unit Tests        | 8      | 12h   | P0        | ⏳ Not Started |
| 2.3 Integration Tests | 8      | 12h   | P0        | ⏳ Not Started |

**Día 10-11 (16h)**:

- Story 2.2 - Tests para todos los services
- Story 2.2 - Tests para validators
- Story 2.2 - Tests para models
- Story 2.2 - Tests para controllers

**Día 12 (8h)**:

- Story 2.3 - Tests de integración Controller+Service
- Story 2.3 - Tests de geometría completa
- Story 2.3 - Tests end-to-end

**Entregables**:

- ✅ Cobertura de tests >80%
- ✅ Tests unitarios completos
- ✅ Tests de integración funcionando

---

### **Fase 5: PyQt6 Compatibility** (1.5 días)

#### Sprint 3.A - Migración PyQt6 (1.5 días)

| Story                   | Puntos | Horas | Prioridad | Status         |
| ----------------------- | ------ | ----- | --------- | -------------- |
| 3.4 PyQt6 Compatibility | 8      | 12h   | P1        | ⏳ Not Started |

**Día 13 (8h)**:

- 08:00-10:00: Story 3.4 - Crear compatibility.py
- 10:00-12:00: Story 3.4 - Implementar detección de Qt version
- 12:00-13:00: 🍽️ Lunch break
- 13:00-15:00: Story 3.4 - Crear imports condicionales
- 15:00-17:00: Story 3.4 - Actualizar imports en archivos

**Día 14 (4h)**:

- 08:00-10:00: Story 3.4 - Testing en Qt5
- 10:00-12:00: Story 3.4 - Testing en Qt6 y documentar

**Entregables**:

- ✅ Compatibilidad Qt5/Qt6
- ✅ Detección automática de versión
- ✅ Tests pasan en ambas versiones

---

### **Fase 6: Polish y Documentación** (1.5 días)

#### Sprint 3.B - Documentación y Mejoras Finales (1.5 días)

| Story              | Puntos | Horas | Prioridad | Status         |
| ------------------ | ------ | ----- | --------- | -------------- |
| 3.1 Documentation  | 5      | 8h    | P1        | ⏳ Not Started |
| 3.2 Variable Names | 2      | 3h    | P2        | ⏳ Not Started |

**Día 15 (8h)**:

- 08:00-10:00: Story 3.1 - Docstrings en funciones
- 10:00-12:00: Story 3.1 - README técnico y guía desarrollo
- 12:00-13:00: 🍽️ Lunch break
- 13:00-15:00: Story 3.1 - Diagramas de arquitectura
- 15:00-17:00: Story 3.2 - Renombrar variables crípticas

**Día 16 (3h)**:

- 08:00-11:00: Review final, checklist de verificación

**Entregables**:

- ✅ Documentación completa
- ✅ Nombres descriptivos
- ✅ Proyecto listo para producción

---

### **Fase 7 (Opcional): Threading UI** (1 día)

#### Sprint 3.C - Performance y UX (1 día - Opcional)

| Story         | Puntos | Horas | Prioridad | Status         |
| ------------- | ------ | ----- | --------- | -------------- |
| 3.3 Threading | 5      | 8h    | P3        | ⏳ Not Started |

**Día 17 (8h)** - OPCIONAL:

- QThread para build_layers
- Progress bar
- Cancelación de operaciones

**Entregables**:

- ✅ UI no se congela
- ✅ Progress feedback

---

### 📊 Resumen de Tiempo por Fase

| Fase                              | Días        | Horas    | Sprint   | Status |
| --------------------------------- | ----------- | -------- | -------- | ------ |
| Fase 0: Pre-Refactorización       | 1           | 8h       | Setup    | ⏳     |
| Fase 1: Fundamentos y Type Safety | 3           | 24h      | Sprint 1 | ⏳     |
| Fase 2: Calidad y DRY             | 2           | 14h      | Sprint 1 | ⏳     |
| Fase 3: Testing Infrastructure    | 2           | 10h      | Sprint 2 | ⏳     |
| Fase 4: Test Coverage             | 3           | 24h      | Sprint 2 | ⏳     |
| Fase 5: PyQt6 Compatibility       | 1.5         | 12h      | Sprint 3 | ⏳     |
| Fase 6: Polish y Documentación    | 1.5         | 11h      | Sprint 3 | ⏳     |
| Fase 7: Threading (Opcional)      | 1           | 8h       | Sprint 3 | ⏳     |
| **TOTAL (sin Fase 7)**            | **14 días** | **103h** |          |        |
| **TOTAL (con Fase 7)**            | **15 días** | **111h** |          |        |

### ⏱️ Duración Estimada del Proyecto

**Trabajo Full-Time**: 14-15 días laborables (~3 semanas)  
**Trabajo Part-Time (4h/día)**: 26-28 días laborables (~5-6 semanas)  
**Trabajo Weekend (8h sábado + 8h domingo)**: 7-8 weekends (~2 meses)

---

### Sprint 1 (1 semana) - Core Refactoring

**Goal**: Arquitectura limpia y type-safe

| Story              | Puntos | Días  | Status         |
| ------------------ | ------ | ----- | -------------- |
| 1.1 Type Hints     | 3      | 0.5   | ⏳ Not Started |
| 1.2 Dataclasses    | 5      | 1     | ⏳ Not Started |
| 1.3 MVC Separation | 8      | 2     | ⏳ Not Started |
| 1.4 DRY Features   | 5      | 1     | ⏳ Not Started |
| 1.5 Logging        | 2      | 0.5   | ⏳ Not Started |
| 1.6 Error Handling | 3      | 1     | ⏳ Not Started |
| **Total**          | **26** | **6** |                |

### Sprint 2 (1 semana) - Testing & Quality

**Goal**: 80%+ test coverage

| Story                 | Puntos | Días  | Status         |
| --------------------- | ------ | ----- | -------------- |
| 2.1 Test Setup        | 3      | 0.5   | ⏳ Not Started |
| 2.2 Unit Tests        | 8      | 2     | ⏳ Not Started |
| 2.3 Integration Tests | 8      | 2     | ⏳ Not Started |
| 2.4 Constants/Config  | 3      | 0.5   | ⏳ Not Started |
| **Total**             | **22** | **5** |                |

### Sprint 3 (2 semanas) - PyQt6, Polish & Threading

**Goal**: Compatibilidad Qt5/6, documentación y UX

| Story                   | Puntos | Días    | Status         |
| ----------------------- | ------ | ------- | -------------- |
| 3.4 PyQt6 Compatibility | 8      | 1.5     | ⏳ Not Started |
| 3.1 Documentation       | 5      | 1.5     | ⏳ Not Started |
| 3.2 Variable Names      | 2      | 0.5     | ⏳ Not Started |
| 3.3 Threading           | 5      | 1       | ⏳ Not Started |
| **Total**               | **20** | **4.5** |                |

---

## ✅ Checklist de Verificación

### Pre-Refactorización

- [x] Plan aprobado
- [ ] Backup del código actual
- [ ] Crear branch `refactor/sprint-1`
- [ ] Skills de Python instaladas

### Durante Refactorización

- [ ] Commits pequeños y frecuentes
- [ ] Tests pasan en cada commit
- [ ] Type checker pasa en cada commit
- [ ] Code review antes de merge

### Post-Refactorización

- [ ] Todos los tests pasan
- [ ] mypy sin errores
- [ ] Coverage > 80%
- [ ] Documentación actualizada
- [ ] Plugin funciona en QGIS 3.x (Qt5)
- [ ] Plugin funciona en QGIS futuras versiones (Qt6)
- [ ] Detección automática de Qt version
- [ ] Output idéntico al original
- [ ] Performance similar o mejor
- [ ] Sin deprecation warnings

---

## 🎓 Principios y Patterns Aplicados

### Python Best Practices

- ✅ Type-first development
- ✅ Dataclasses for structured data
- ✅ NewType for domain primitives
- ✅ Frozen dataclasses (immutability)
- ✅ Protocol for interfaces

### Design Patterns

- ✅ KISS - Keep It Simple
- ✅ Single Responsibility Principle
- ✅ Separation of Concerns
- ✅ Composition over Inheritance
- ✅ DRY - Don't Repeat Yourself

### PyQt6 Patterns

- ✅ MVC Architecture
- ✅ Signal/Slot communication
- ✅ No business logic in UI
- ✅ Threaded operations (Sprint 3)

---

## 📊 Métricas de Éxito

| Métrica                 | Antes | Meta | Actual |
| ----------------------- | ----- | ---- | ------ |
| Líneas de código        | ~600  | ~850 | -      |
| Type coverage           | 0%    | 100% | -      |
| Test coverage           | 0%    | 80%+ | -      |
| Duplicación             | ~30%  | <5%  | -      |
| Cyclomatic complexity   | ~15   | <10  | -      |
| Clases con SRP          | 0/3   | 6/6  | -      |
| Excepciones silenciosas | 4     | 0    | -      |
| Magic numbers           | ~10   | 0    | -      |
| Qt5 compatibility       | ✅    | ✅   | -      |
| Qt6 compatibility       | ❌    | ✅   | -      |

---

## 🔒 Reglas Inviolables

### ✅ PERMITIDO

- Agregar type hints
- Extraer funciones y clases
- Renombrar variables
- Agregar validaciones
- Agregar logging
- Agregar tests
- Reorganizar estructura de archivos
- Agregar documentación

### ❌ PROHIBIDO

- Modificar fórmulas matemáticas
- Cambiar cálculos geométricos
- Alterar algoritmos de proyección
- Cambiar orden de operaciones geométricas
- Modificar valores de constantes geométricas (a, b, h, r, etc.)
- Cambiar lógica de QgsGeometryUtils
- Alterar construcción de QgsPolygon/QgsLineString

---

## 📝 Notas Adicionales

### Estrategia de Compatibilidad PyQt5/PyQt6

Para mantener compatibilidad con ambas versiones de Qt, implementaremos un módulo de compatibilidad:

```python
# qBRA/compatibility.py
"""
Qt5/Qt6 compatibility layer for QGIS plugins.
Supports both PyQt5 (QGIS 3.x) and PyQt6 (future QGIS versions).
"""
import sys
from typing import Any

# Detect Qt version
try:
    from qgis.PyQt import QtCore
    QT_VERSION = QtCore.QT_VERSION_STR
    QT_MAJOR = int(QT_VERSION.split('.')[0])
except ImportError:
    QT_VERSION = "unknown"
    QT_MAJOR = 5  # Default to Qt5

IS_QT5 = QT_MAJOR == 5
IS_QT6 = QT_MAJOR == 6

# Conditional imports
if IS_QT6:
    from qgis.PyQt.QtCore import Qt
    # Qt6: Enums moved to their respective classes
    AlignLeft = Qt.AlignmentFlag.AlignLeft
    AlignRight = Qt.AlignmentFlag.AlignRight
    LeftDockWidgetArea = Qt.DockWidgetArea.LeftDockWidgetArea
    RightDockWidgetArea = Qt.DockWidgetArea.RightDockWidgetArea
else:
    from qgis.PyQt.QtCore import Qt
    # Qt5: Enums are directly in Qt namespace
    AlignLeft = Qt.AlignLeft
    AlignRight = Qt.AlignRight
    LeftDockWidgetArea = Qt.LeftDockWidgetArea
    RightDockWidgetArea = Qt.RightDockWidgetArea

# Export all compatibility constants
__all__ = [
    'IS_QT5',
    'IS_QT6',
    'QT_VERSION',
    'AlignLeft',
    'AlignRight',
    'LeftDockWidgetArea',
    'RightDockWidgetArea',
]
```

**Uso en el código**:

```python
# Antes (solo Qt5):
from qgis.PyQt.QtCore import Qt
self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

# Después (compatible Qt5/Qt6):
from qBRA.compatibility import LeftDockWidgetArea, RightDockWidgetArea
self.setAllowedAreas(LeftDockWidgetArea | RightDockWidgetArea)
```

### Dependencias

- QGIS API (no cambiar versión)
- PyQt5/PyQt6 (versión de QGIS, auto-detectada)
- pytest (nuevo)
- mypy (nuevo)

### Riesgos

1. **Cambios en output**: Mitigación → tests de regresión comparando output
2. **Breaking changes**: Mitigación → tests completos antes de merge
3. **Performance**: Mitigación → benchmarks antes/después

### Siguientes Pasos

1. ✅ Revisar y aprobar este plan
2. ⏳ Crear branch de refactorización
3. ⏳ Iniciar Sprint 1, Story 1.1

---

## 📈 Progreso del Proyecto

### Estado Actual: � Sprint 1 en Progreso (88% completado)

**Última actualización**: 4 de marzo, 2026

### Estadísticas

| Categoría           | Total | Completadas | En Progreso | Pendientes |
| ------------------- | ----- | ----------- | ----------- | ---------- |
| **Fases**           | 7     | 0           | 1           | 6          |
| **Sprints**         | 3     | 0           | 1           | 2          |
| **Stories**         | 13    | 5           | 0           | 8          |
| **Story Points**    | 68    | 23          | 0           | 45         |
| **Horas Estimadas** | 111h  | 19h         | 0h          | 92h        |

### Progreso por Sprint

**Sprint 1: Core Refactoring**

- ✅✅✅✅✅✅✅✅⬜⬜ 88% (23/26 SP)
  - ✅ Story 1.1: Type Hints (3 SP)
  - ✅ Story 1.2: Dataclasses (5 SP)
  - ✅ Story 1.3: MVC Separation (8 SP)
  - ✅ Story 1.4: DRY Feature Creation (5 SP)
  - ✅ Story 1.5: Logging (2 SP)
  - ⬜ Story 1.6: Error Handling (3 SP)

**Sprint 2: Testing & Quality**

- ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0% (0/22 SP)

**Sprint 3: PyQt6, Polish & Threading**

- ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0% (0/20 SP)

### Próximos Pasos

1. ✅ Aprobar plan de refactorización
2. ⏳ Crear branch `refactor/main`
3. ⏳ Iniciar Fase 0: Pre-Refactorización
4. ⏳ Comenzar Sprint 1, Story 1.1

---

**Fin del Plan de Refactorización**

_Documento vivo - Se actualizará según progreso_

---

## 🔄 Historial de Cambios

### v1.1 - 4 de marzo, 2026

- ✅ Agregadas fases detalladas con cronograma día a día
- ✅ Agregados tiempos estimados por fase (103-111 horas)
- ✅ Agregada Story 3.4: Migración PyQt6 con compatibilidad Qt5
- ✅ Agregado módulo de compatibilidad Qt5/Qt6
- ✅ Actualizada estructura de archivos con compatibility.py
- ✅ Actualizado roadmap con Sprint 3 extendido
- ✅ Agregada sección de progreso del proyecto

### v1.0 - 4 de marzo, 2026

- ✅ Plan inicial de refactorización creado
- ✅ Análisis de bugs y code smells completado
- ✅ Definidas 12 stories en 3 sprints
- ✅ Establecidos objetivos y métricas
