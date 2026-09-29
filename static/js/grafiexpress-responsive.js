/*
 * Ajustes responsivos globales de GrafiExpress (ver css/grafiexpress-responsive.css).
 *
 * - Tablas de filtros (formularios armados como tabla, sin <thead>): se marcan
 *   con .gx-filter para que en celular se apilen en una sola columna.
 * - Resto de tablas (resultados, detalles, inlines): se envuelven en un
 *   contenedor con scroll horizontal propio para que no desborden la página.
 */
(function ($) {
    'use strict';

    function esTablaDeFiltros($t) {
        return $t.find('> thead').length === 0 &&
               $t.closest('form').length > 0 &&
               $t.find('input:not([type=hidden]), select').length > 0 &&
               $t.find('> tbody > tr').length <= 12 &&
               $t.attr('id') !== 'result_list';
    }

    // En celular los filtros arrancan plegados detrás de un botón que muestra
    // cuántos están activos.
    function plegarFiltros($t) {
        var activos = $t.find('input[type=text], input[type=date], input:not([type]), select').filter(function () {
            var v = $(this).val();
            return v && v !== 'TODOS' && v !== '';
        }).length;
        var $btn = $('<button type="button" class="btn btn-default gx-filter-toggle">' +
                     '<i class="fa fa-filter"></i> Filtros' +
                     (activos ? '<span class="badge gx-badge">' + activos + '</span>' : '') +
                     '<i class="fa fa-chevron-down gx-chevron"></i></button>');
        $t.addClass('gx-collapsed');
        $btn.on('click', function () {
            $t.toggleClass('gx-collapsed');
            $btn.find('.fa-chevron-down, .fa-chevron-up').toggleClass('fa-chevron-down fa-chevron-up');
            // chosen/select2 calculan su ancho al mostrarse
            $t.find('.chosen-select').trigger('chosen:updated');
        });
        $t.before($btn);
    }

    function ajustarTablas(contexto) {
        $(contexto).find('table').each(function () {
            var $t = $(this);
            if ($t.data('gx-listo')) {
                return;
            }
            $t.data('gx-listo', true);

            if ($t.hasClass('table-filter') && esTablaDeFiltros($t)) {
                $t.addClass('gx-filter');
                plegarFiltros($t);
                return;
            }
            // Solo la tabla más externa necesita scroll; las anidadas viajan dentro
            if ($t.parents('table, .gx-table-scroll, .table-responsive').length === 0) {
                $t.wrap('<div class="gx-table-scroll"></div>');
            }
        });
    }

    function iniciar() {
        ajustarTablas('#id_content');

        // Las filas que agregan los inlines del admin ("Agregar otro") o por AJAX
        $(document).on('formset:added', function (e, $fila) {
            ajustarTablas($fila || document);
        });
    }

    // Listener nativo y no $(fn): en jQuery 1.x un error en otro callback de
    // "ready" de la página cancela los siguientes, y esto tiene que correr igual.
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciar);
    } else {
        iniciar();
    }
})(window.jQuery || window.django.jQuery);
