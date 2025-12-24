/**
 FILTROS DE LA TABLA DE CCPP
 */
function initializeTablaCCPP() {
    const cuerpoTabla = document.getElementById('data-table-body');
    if (!cuerpoTabla) return;

    try {
        const filas = Array.from(cuerpoTabla.querySelectorAll('tr'));
        const columnaOrden = document.getElementById('sort-column');
        const direccionOrden = document.getElementById('sort-direction');
        const controlesFiltro = document.querySelectorAll('.control-input');
        const botonReset = document.getElementById('reset-controls');

        const filaSinResultados = crearFilaSinResultados();

        /**
         * Crea dinámicamente la fila de "No hay resultados"
         */
        function crearFilaSinResultados() {
            let fila = document.getElementById('no-results-row');
            if (!fila) {
                fila = document.createElement('tr');
                fila.id = 'no-results-row';
                fila.innerHTML = `
                    <td colspan="4" class="py-10 text-center text-gray-400">
                        No hay resultados que coincidan con los filtros.
                    </td>`;
                fila.style.display = 'none';
            }
            return fila;
        }

        /**
         * Ordena las filas según columna y dirección
         */
        function ordenarFilas(columna, direccion) {
            if (!columna) return;

            const esNumerica = ['id_ccpp', 'cantidad_anos', 'fecha_entrega'].includes(columna);

            filas.sort((a, b) => {
                let valorA = a.getAttribute(`data-${columna}`) || '';
                let valorB = b.getAttribute(`data-${columna}`) || '';

                if (esNumerica) {
                    valorA = parseFloat(valorA);
                    valorB = parseFloat(valorB);
                    valorA = isNaN(valorA) ? (direccion === 'asc' ? Infinity : -Infinity) : valorA;
                    valorB = isNaN(valorB) ? (direccion === 'asc' ? Infinity : -Infinity) : valorB;
                } else {
                    valorA = valorA.toLowerCase();
                    valorB = valorB.toLowerCase();
                }

                return direccion === 'asc' ? valorA - valorB : valorB - valorA;
            });
        }

        /**
         * Aplica filtros y ordenamiento, y renderiza la tabla
         */
        function aplicarFiltrosYOrden() {
            const columnaActual = columnaOrden.value;
            const direccionActual = direccionOrden.value;
            const filtros = {};

            controlesFiltro.forEach(control => {
                const columna = control.getAttribute('data-column');
                const valor = control.value.toLowerCase().trim();
                if (columna && valor) filtros[columna] = valor;
            });

            let filasVisibles = 0;
            const fragmento = document.createDocumentFragment();

            filas.forEach(fila => {
                let coincide = true;

                for (const columna in filtros) {
                    const valorFiltro = filtros[columna];
                    let valorFila = fila.getAttribute(`data-${columna}`) || '';
                    valorFila = valorFila.toLowerCase();

                    if (columna === 'residencial') {
                        if (!valorFila.includes(valorFiltro)) {
                            coincide = false;
                            break;
                        }
                    } else {
                        if (valorFila !== valorFiltro) {
                            coincide = false;
                            break;
                        }
                    }
                }

                fila.style.display = coincide ? '' : 'none';
                if (coincide) filasVisibles++;
            });

            if (columnaActual) ordenarFilas(columnaActual, direccionActual);

            cuerpoTabla.innerHTML = '';
            filas.forEach(fila => {
                if (fila.style.display !== 'none') fragmento.appendChild(fila);
            });
            cuerpoTabla.appendChild(fragmento);

            if (filasVisibles === 0) {
                filaSinResultados.style.display = '';
                if (!document.getElementById('no-results-row')) {
                    cuerpoTabla.appendChild(filaSinResultados);
                }
            } else {
                filaSinResultados.style.display = 'none';
            }
        }

        /**
         * Restablece los controles de filtro y ordenamiento
         */
        function resetearControles() {
            controlesFiltro.forEach(control => {
                control.value = '';
            });
            columnaOrden.value = '';
            direccionOrden.value = 'asc';
            aplicarFiltrosYOrden();
        }

        // Eventos
        controlesFiltro.forEach(control => {
            control.addEventListener('input', aplicarFiltrosYOrden);
        });
        columnaOrden.addEventListener('change', aplicarFiltrosYOrden);
        direccionOrden.addEventListener('change', aplicarFiltrosYOrden);
        botonReset.addEventListener('click', resetearControles);

        // Inicialización
        aplicarFiltrosYOrden();

    } catch (error) {
        console.error("Error al inicializar la tabla CCPP:", error);
    }
}

// Ejecuta la lógica al cargar el DOM
document.addEventListener('DOMContentLoaded', initializeTablaCCPP);




/** 
 * CALCULAR PERIODOS 
 */
function calcularPeriodo() {
    const fechaEntregaInput = document.getElementById('id_fecha_entrega');
    const cantAnosInput = document.getElementById('id_cant_anos');
    const periodoDisplay = document.getElementById('periodo_display');
    const hiddenPeriodo = document.getElementById('hidden_id_periodo');

    const fechaStr = fechaEntregaInput.value;
    const cantAnos = parseInt(cantAnosInput.value, 10);
    
    let periodoCalculado = '-';
    let valorParaEnvio = '';

    if (fechaStr && !isNaN(cantAnos) && cantAnos >= 0) {
        try {
            // Extraer el año de la fecha de entrega (formato YYYY-MM-DD)
            const anoInicio = parseInt(fechaStr.substring(0, 4), 10);
            
            // Calcular el año final (año de inicio + cantidad de años)
            const anoFin = anoInicio + cantAnos;
            
            periodoCalculado = `${anoInicio}-${anoFin}`;
            valorParaEnvio = periodoCalculado;
            
        } catch (e) {
            console.error("Error al calcular el período:", e);
        }
    }
    
    // Actualiza el campo de solo visualización
    periodoDisplay.textContent = periodoCalculado;

    // **Muy importante:** Actualiza el campo oculto para que el valor se envíe al servidor
    hiddenPeriodo.value = valorParaEnvio;
}

// Asocia la función a los eventos de cambio en ambos campos
document.addEventListener('DOMContentLoaded', () => {
    const fechaEntregaInput = document.getElementById('id_fecha_entrega');
    const cantAnosInput = document.getElementById('id_cant_anos');
    
    // Llama a la función al cargar la página por si hay valores precargados
    calcularPeriodo(); 

    fechaEntregaInput.addEventListener('change', calcularPeriodo);
    fechaEntregaInput.addEventListener('keyup', calcularPeriodo); // Por si se escribe manualmente

    cantAnosInput.addEventListener('input', calcularPeriodo);
});



/** 
 MODAL DE CONFIRMACIÓN DE ELIMINACIÓN EDITAR CCPP
/**
     * @param {string} ccppName - El nombre del CCPP a eliminar.
     */
    function openDeleteModal(ccppName) {
        // 1. Mostrar el nombre del CCPP en el modal
        const ccppNameElement = document.getElementById('ccpp-name');
        if (ccppNameElement) {
            ccppNameElement.textContent = ccppName || 'este CCPP';
        }

        // 2. Mostrar el modal
        const modal = document.getElementById('delete-modal');
        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');

        // 3. Establecer el foco en el botón de Cancelar (ya tiene autofocus, pero esto asegura la compatibilidad)
        document.getElementById('cancel-delete-button').focus();
    }

    /**
     * Cierra el modal de confirmación de eliminación.
     */
    function closeDeleteModal() {
        const modal = document.getElementById('delete-modal');
        modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    // Manejo de teclado global para el modal (Esc para cerrar)
    document.addEventListener('keydown', function(event) {
        const modal = document.getElementById('delete-modal');
        const isModalOpen = !modal.classList.contains('hidden');

        if (isModalOpen) {
            // Cierra el modal al presionar ESC
            if (event.key === 'Escape') {
                closeDeleteModal();
            }
        }
    });



// --- NUEVAS FUNCIONES PARA EL MODAL DE CLONAR ---
/**
 * Abre el modal de confirmación para clonar una CCPP.
 * @param {string} ccppName - El nombre del CCPP a mostrar en el modal.
 */
function openCloneModal(ccppName) {
    // 1. Asigna el nombre del CCPP al span dentro del modal
    document.getElementById('ccpp-clone-name').textContent = ccppName;
    
    // 2. Muestra el modal eliminando la clase 'hidden'
    document.getElementById('clone-modal').classList.remove('hidden');
    
    // 3. ENFOCAR EL BOTÓN CANCELAR (usando la función de enfoque)
    document.getElementById('cancel-clone-button').focus();
}

/**
 * Cierra el modal de confirmación para clonar.
 */
function closeCloneModal() {
    // Oculta el modal añadiendo la clase 'hidden'
    document.getElementById('clone-modal').classList.add('hidden');
}

// ... Las funciones openDeleteModal y closeDeleteModal existentes permanecen iguales ...