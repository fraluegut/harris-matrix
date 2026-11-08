# Modelo de datos de estratigrafía arqueológica (borrador)

Borrador escrito desde conocimiento general. **No está contrastado** con la bibliografía ni con un arqueólogo de campo: el vocabulario y las reglas hay que revisarlos antes de fijar la versión 1.

## 1. Principios

- **Registro y derivación separados.** Se guardan hechos observados (relaciones físicas, medidas, dataciones); el orden temporal, las fases y el gráfico se derivan.
- **Toda afirmación lleva certeza y fuente** (segura, probable, dudosa).
- **Ausencia de relación no es contemporaneidad.**
- **Una UE no es una fecha.** La cronología son afirmaciones de datación.
- **Verificable**, con informe que explica qué fila falla y por qué.
- **Ficheros abiertos**: un CSV por entidad, UTF-8, identificadores estables.

## 2. Visión general

Todas las tablas se unen a la UE por `ue_id`: `relaciones` (UE con UE), `puntos` y `geometrias`, `hallazgos` (y tablas especializadas), `muestras`, `fotos` y `dibujos`, `dataciones` y `agrupaciones`. `dataciones` también se aplica a hallazgos, muestras y fases.

## 3. Unidad estratigráfica (`ues`)

| Campo | Tipo | Obligatorio | Notas |
| --- | --- | --- | --- |
| `ue_id` | texto | sí | Clave única en el yacimiento. Texto, para admitir "1045b". |
| `yacimiento` | texto | sí | Para unir campañas. |
| `area`, `sector`, `cuadro` | texto | no | Localización. |
| `tipo_unidad` | vocabulario | sí | `deposito`, `interfaz`, `estructura`, `virtual`. |
| `subtipo` | vocabulario | no | Corte, fosa, zanja, muro, suelo, relleno, derrumbe... |
| `descripcion` | texto | sí | Lo observado, sin interpretar. |
| `interpretacion` | texto | no | Lo inferido. |
| `estado_excavacion` | vocabulario | sí | `sin_excavar`, `parcial`, `excavada`, `solo_documentada`. |
| `fecha_inicio`, `fecha_fin` | fecha ISO | no | Fechas de excavación. |
| `responsable` | texto | no | |
| `fiabilidad` | vocabulario | no | buena, regular, deficiente. |
| `notas` | texto | no | |

`deposito` = unidad positiva; `interfaz` = unidad negativa; `estructura` = unidad construida; `virtual` = reconstruida, no excavada (Extended Matrix).

Atributos físicos según tipo (color, textura, compactación; forma, perfil, bordes; material, aparejo...): propuesta de tabla en formato largo `ue_atributos` (`ue_id`, `atributo`, `valor`). Pendiente de decidir.

## 4. Posición espacial (`puntos`, `geometrias`, `sistemas_referencia`)

- `sistemas_referencia`: sistema global (EPSG) o local con su transformación; datum vertical.
- `puntos`: `punto_id`, `ue_id`, `rol` (`cota_superior`, `cota_inferior`, `centro`, `limite`, `esquina`, `hallazgo`), `x`, `y`, `z` (m), `sistema_id`, `metodo` (`estacion_total`, `gnss`, `cinta`, `fotogrametria`, `estimado`), `precision_m`, `fecha_medicion`.
- `geometrias`: polígono en planta o sección (WKT/GeoJSON) con `ue_id`, `tipo` (`planta`, `seccion`, `limite_conjetural`), `sistema_id`, `metodo`.
- Derivados, no guardados: cotas medias, espesor, área, volumen aproximado, profundidad respecto a un datum.

## 5. Relaciones (`relaciones`, `vocabulario_relaciones`)

`relaciones`: `rel_id`, `ue_origen`, `tipo`, `ue_destino`, `certeza`, `fuente` (`campo`, `seccion`, `fotografia`, `inferencia`, `otro`), `observado_por`, `fecha`, `notas`. Cada relación se escribe una vez; la inversa la genera el sistema.

| Tipo | Inversa | Efecto temporal | Origen admitido | Destino admitido |
| --- | --- | --- | --- | --- |
| `cubre` | `cubierto_por` | origen posterior a destino | depósito, estructura | cualquiera |
| `corta` | `cortado_por` | origen posterior a destino | interfaz | cualquiera |
| `rellena` | `relleno_por` | origen posterior a destino | depósito | interfaz |
| `se_apoya_en` | `soporta` | origen posterior a destino | depósito, estructura | cualquiera |
| `se_une_a` | `se_une_a` | contemporáneos | estructura | estructura |
| `igual_a` | `igual_a` | misma unidad registrada dos veces | cualquiera | mismo tipo |
| `posterior_a` | `anterior_a` | origen posterior, sin contacto físico | cualquiera | cualquiera |

- Los tipos son filas del vocabulario, no código: adaptables a cada escuela.
- `igual_a` fusiona nodos; no genera flecha.
- No se infiere contemporaneidad de la ausencia de relación.

## 6. Cronología (`dataciones`)

Afirmaciones de datación sobre un objeto (`ue`, `hallazgo`, `muestra`, `fase`, `agrupacion`): `datacion_id`, `objeto_tipo`, `objeto_id`, `metodo` (`radiocarbono`, `dendrocronologia`, `termoluminiscencia`, `arqueomagnetismo`, `tipologia`, `numismatica`, `epigrafia`, `documental`, `otro`), `significado` (`evento`, `post_quem`, `ante_quem`, `uso`), `asociacion` (`contemporaneo`, `residual`, `intrusivo`, `desconocida`), `anio_inicio`, `anio_fin` (año astronómico con signo), `incertidumbre`, `edad_14c`, `error_14c`, `curva_calibracion`, `laboratorio_ref`, `certeza`, `referencia`.

Lo datado no es el contexto: `asociacion` lo hace explícito.

## 7. Materiales asociados

`hallazgos` (común) y especializadas `ceramica`, `litico`, `fauna`, `restos_humanos` (datos sensibles); `muestras`; `fotos` + `foto_objetos` (vínculo foto-objeto); `dibujos`. Las dataciones de hallazgos y muestras van en `dataciones`.

## 8. Agrupaciones (`agrupaciones`, `agrupacion_ue`)

Niveles: `actividad`, `estructura`, `espacio`, `fase`, `periodo`. `agrupaciones`: `agrupacion_id`, `tipo`, `nombre`, `descripcion`, `padre_id`, `certeza`. Una UE puede estar en varias agrupaciones de tipos distintos, pero en una sola fase. Las fases se proponen desde el grafo y se confirman a mano.

## 9. Verificación (`verify`)

Severidades: **error**, **aviso**, **info**. Código de salida distinto de cero si hay errores.

| Regla | Comprueba | Severidad |
| --- | --- | --- |
| R01 | `ue_id` duplicado | error |
| R02 | Referencia a UE inexistente | error |
| R03 | Tipo de relación fuera del vocabulario | error |
| R04 | Relación entre tipos de unidad no admitidos | error |
| R05 | UE relacionada consigo misma | error |
| R10 | Ciclo en el grafo temporal (con el camino) | error |
| R11 | Contradicción directa (A cubre B y B cubre A) | error |
| R12 | Ciclo al fusionar `igual_a` | error |
| R13 | `igual_a` entre tipos distintos | aviso |
| R14 | Corte sin relleno o relleno sin corte | aviso |
| R15 | UE sin relaciones | aviso |
| R16 | Relación redundante por transitividad | info |
| R17 | Inversa escrita en ambos sentidos con datos distintos | aviso |
| R20 | Cota inferior mayor que la superior | error |
| R21 | Geometría inválida o fuera del yacimiento | error |
| R22 | A cubre a B pero está claramente por debajo (con tolerancia) | aviso |
| R23 | A cubre o corta a B pero los polígonos no se tocan | aviso |
| R30 | Datación de UE anterior más reciente que la de una posterior | error si ambas seguras; aviso si no |
| R31 | `post_quem` posterior a `ante_quem` en la misma UE | error |
| R32 | Fase incoherente con el orden | error |
| R33 | UE datada con objeto residual o intrusivo | aviso |
| R34 | Datación propagada por la secuencia que deja intervalo vacío | error |

Las dataciones se propagan por el grafo. Las reglas espaciales son avisos, con tolerancias configurables. Informe en texto y JSON.

## 10. Salida gráfica (`render`)

SVG editable: un nodo por UE (o grupo `igual_a`), forma según tipo, filas por nivel de secuencia, trazo según certeza (continuo, discontinuo, punteado), bandas por fase opcionales, ciclos en rojo con `--errores`. Capas con nombre; nodos con `id="ue-1045"` y `data-tipo`, `data-fase`, `data-certeza`; estilos en el propio fichero. Disposición inicial con Graphviz (opcional) y más adelante algoritmo propio. Otras salidas: DOT, GraphML, CSV con el orden calculado. El SVG es solo de salida.

## 11. Ficheros y compatibilidad

Carpeta de proyecto con `proyecto.json` (nombre, yacimiento, `version_esquema`, tolerancias) y un CSV por tabla. UTF-8, coma, punto decimal, fechas ISO 8601, identificadores como texto. Adaptador hmdp: `contexts` ↔ `ues`, `observations` ↔ `relaciones`, `inferences` ↔ `igual_a`, `phases`/`periods` ↔ `agrupaciones`, `events` ↔ `dataciones` (con pérdida de certeza, fuente, posición y materiales).

## 12. Arqueología paramental

Pendiente de diseñar: en alzados y muros la relación se observa sobre un paramento, y conviene registrar la cara y la posición en el muro (UEM), tipos de relación específicos (trabado, adosado, cortado por apertura, reparación) y la agrupación en elementos constructivos y fases constructivas. El modelo base debe admitir esto sin cambios estructurales.

## 13. Preguntas abiertas

- Vocabulario de relaciones: ¿suficiente? ¿qué falta (traba con, gravita sobre...)?
- Convención: ¿UE de contexto único estricto o también unidades murarias (UEM/USM)? ¿Se mantiene `virtual`?
- Atributos físicos: ¿columnas por tipo o formato largo?
- Identificadores: ¿únicos por yacimiento o por campaña?
- Cronología: ¿año astronómico con signo o a.C./d.C.? ¿Se guardan datos de calibración?
- Fases: ¿propuestas automáticas o solo registradas?
- Espacio: tolerancias R22 y R23; ¿hace falta 3D?
- Restos humanos: ¿esquema común o separado?
- SVG: ¿solo salida o importar cambios?
- Bibliografía: contrastar con las fuentes originales antes de la v1.
- Licencia.
