/**
* Gestión de la Notificación de Éxito
*/
function showNotification() {
    const notification = document.getElementById('success-notification');
    if (notification) {
        // ** CORRECCIÓN: Retraso de 50ms para evitar el bloqueo del clic **
        setTimeout(() => { 
            notification.classList.remove('opacity-0', 'translate-y-4');
            notification.classList.add('opacity-100', 'translate-y-0');
            
            // Oculta automáticamente después de 5 segundos
            setTimeout(hideNotification, 5000); 
        }, 50); 
    }
}

function hideNotification() {
    const notification = document.getElementById('success-notification');
    if (notification) {
        notification.classList.remove('opacity-100', 'translate-y-0');
        notification.classList.add('opacity-0', 'translate-y-4');
        
        // ** CORRECCIÓN: Eliminar completamente la notificación después de la animación **
        setTimeout(() => {
            if (notification && notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }
}

/**
* Lógica de Filtrado y Ordenamiento de la Tabla
*/
function initializeDataTableLogic() {
    const tableBody = document.getElementById('data-table-body');
    
    if (!tableBody) {
        return;
    }

    try {
        const rows = Array.from(tableBody.querySelectorAll('tr'));
        const sortColumn = document.getElementById('sort-column');
        const sortDirection = document.getElementById('sort-direction');
        const filterControls = document.querySelectorAll('.control-input');
        const resetButton = document.getElementById('reset-controls');

        // Crear dinámicamente la fila de "No hay resultados"
        const createNoResultsRow = () => {
            let noResultsRow = document.getElementById('no-results-row');
            if (!noResultsRow) {
                noResultsRow = document.createElement('tr');
                noResultsRow.id = 'no-results-row';
                // Nota: el colspan debe coincidir con el número de columnas (5 en este caso)
                noResultsRow.innerHTML = '<td colspan="5" class="py-10 text-center text-gray-400">No hay resultados que coincidan con los filtros.</td>'; 
                noResultsRow.style.display = 'none';
            }
            return noResultsRow;
        };

        const noResultsRow = createNoResultsRow();

        // Lógica de Ordenamiento
        function sortRows(column, direction) {
            if (!column) return;
            const isNumeric = column === 'doc';

            rows.sort((rowA, rowB) => {
                let valueA = rowA.getAttribute(`data-${column}`) || '';
                let valueB = rowB.getAttribute(`data-${column}`) || '';

                if (isNumeric) {
                    valueA = parseFloat(valueA);
                    valueB = parseFloat(valueB);
                    // Asegura que los valores nulos o no numéricos se manejen correctamente en el orden
                    valueA = isNaN(valueA) ? (direction === 'asc' ? Infinity : -Infinity) : valueA;
                    valueB = isNaN(valueB) ? (direction === 'asc' ? Infinity : -Infinity) : valueB;
                } else {
                    valueA = valueA.toLowerCase();
                    valueB = valueB.toLowerCase();
                }

                if (valueA < valueB) {
                    return direction === 'asc' ? -1 : 1;
                }
                if (valueA > valueB) {
                    return direction === 'asc' ? 1 : -1;
                }
                return 0;
            });
        }

        // Lógica de Filtrado y Renderizado
        function applyFiltersAndSort() {
            const currentSortColumn = sortColumn.value;
            const currentSortDirection = sortDirection.value;
            const filters = {};
            
            filterControls.forEach(control => {
                const column = control.getAttribute('data-column');
                let value = control.value;
                if (column && value) {
                    filters[column] = value.toLowerCase().trim();
                }
            });

            let visibleRowCount = 0;
            const fragment = document.createDocumentFragment();

            // 2. APLICAR FILTROS
            rows.forEach(row => {
                let isMatch = true;

                for (const column in filters) {
                    const filterValue = filters[column];
                    let rowValue = row.getAttribute(`data-${column}`) || '';
                    rowValue = rowValue.toLowerCase();

                    if (filterValue === '') continue;

                    if (column === 'descripcion' || column === 'observacion' || column === 'capitulo') {
                        // Filtro de búsqueda de texto (contiene)
                        if (!rowValue.includes(filterValue)) {
                            isMatch = false;
                            break;
                        }
                    } else {
                        // Filtro de selección (coincidencia exacta: unidad, doc)
                        if (rowValue !== filterValue) {
                            isMatch = false;
                            break;
                        }
                    }
                }

                if (isMatch) {
                    // Ocultar/mostrar usando CSS: importante para el reordenamiento posterior
                    row.style.display = ''; 
                    visibleRowCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            // 3. APLICAR ORDENAMIENTO (solo a las filas filtradas/visibles)
            if (currentSortColumn) {
                sortRows(currentSortColumn, currentSortDirection);
            }

            // 4. RE-RENDERIZAR LA TABLA (Mover las filas ordenadas al DOM)
            while (tableBody.firstChild) {
                tableBody.removeChild(tableBody.firstChild);
            }
            
            rows.forEach(row => {
                if (row.style.display !== 'none') {
                    fragment.appendChild(row);
                }
            });
            
            tableBody.appendChild(fragment);

            // 5. MOSTRAR MENSAJE de NO RESULTADOS
            if (visibleRowCount === 0) {
                noResultsRow.style.display = '';
                tableBody.appendChild(noResultsRow);
            } else {
                noResultsRow.style.display = 'none';
            }
        }

        // Resetear Controles
        function resetControls() {
            filterControls.forEach(control => {
                if (control.tagName === 'SELECT') {
                    // Establece el valor a la opción por defecto ("")
                    control.value = ''; 
                } else if (control.tagName === 'INPUT') {
                    control.value = '';
                }
            });
            sortColumn.value = '';
            sortDirection.value = 'asc';
            
            applyFiltersAndSort();
        }

        // Event Listeners
        filterControls.forEach(control => {
            control.addEventListener('input', applyFiltersAndSort);
        });

        sortColumn.addEventListener('change', applyFiltersAndSort);
        sortDirection.addEventListener('change', applyFiltersAndSort);
        resetButton.addEventListener('click', resetControls);

        // Inicialización: Aplicar filtros y orden inicial
        applyFiltersAndSort(); 
        
    } catch (error) {
        console.error("Error al inicializar la lógica de la tabla:", error);
    }
}

// Ejecuta toda la lógica al cargar el contenido
document.addEventListener('DOMContentLoaded', function() {
    // Inicializa la notificación si existe
    const notification = document.getElementById('success-notification');
    if (notification) {
        showNotification();
    }
    
    // Inicializa la lógica de la tabla de forma segura
    initializeDataTableLogic();
});





/**
* Formatea el campo 'Doc' al formato 00-00-00 y restringe la entrada solo a dígitos.
* @param {HTMLInputElement} input - El elemento input.
*/
function formatDocInput(input) {
    // 1. Limpia la entrada: Elimina todo lo que no sea un dígito (bloquea letras)
    let value = input.value.replace(/[^0-9]/g, '');
    
    // 2. Formatea la entrada: Agrega guiones automáticamente
    if (value.length > 2) {
        value = value.substring(0, 2) + '-' + value.substring(2);
    }
    if (value.length > 5) {
        value = value.substring(0, 5) + '-' + value.substring(5, 7); // Limita a 8 caracteres totales (6 dígitos, 2 guiones)
    }
    
    // 3. Aplica el valor formateado y corta a la longitud máxima (8)
    input.value = value.substring(0, 8);
}

// Opcional: Evitar pegar caracteres no numéricos
document.getElementById('id_doc').addEventListener('paste', function(e) {
    const clipboardData = e.clipboardData || window.clipboardData;
    const pastedData = clipboardData.getData('Text');
    // Si lo pegado contiene caracteres no numéricos (o guiones ya que se añaden)
    if (/[^0-9-]/.test(pastedData)) {
        e.preventDefault();
    }
    // Ejecutar la función de formateo después de un breve retraso para procesar lo pegado
    setTimeout(() => formatDocInput(this), 0);
});




// La función para ocultar el error se mantiene
function hideDbError() {
    const alert = document.getElementById('db-error-alert');
    if (alert) {
        alert.style.display = 'none';
    }
}

// --- LÓGICA DEL MODAL DE ELIMINACIÓN ---

const deleteModal = document.getElementById('delete-modal');
const cancelButton = document.getElementById('cancel-delete-button');
const confirmButton = document.getElementById('confirm-delete-button');
const form = document.getElementById('delete-unidad-form'); // Usamos el formulario de eliminación


/**
 * Muestra el modal de confirmación y enfoca el botón 'Cancelar'.
 * @param {Event} e - El evento de click del botón.
 */
function showDeleteModal(e) {
    e.preventDefault(); // Detiene el envío del formulario inmediatamente
    
    // 1. Mostrar el modal
    deleteModal.classList.remove('hidden');
    
    // 2. Enfocar el botón 'Cancelar' por defecto 
    //    (Se ha añadido 'autofocus' en el HTML, esta línea es redundante/opcional pero se mantiene como backup)
    cancelButton.focus(); 
    
    // 3. Reemplazar el listener del botón de confirmación
    confirmButton.onclick = function() {
        // El formulario de eliminación ya tiene el campo action_type='delete' en el botón
        form.submit(); // Envía el formulario de eliminación
    };
}

/**
 * Oculta el modal de confirmación.
 */
function closeDeleteModal() {
    deleteModal.classList.add('hidden');
}

// Cierra el modal al presionar la tecla ESC
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && !deleteModal.classList.contains('hidden')) {
        closeDeleteModal();
    }
});


