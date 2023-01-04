odoo.define('metro_gate_management.picking_kanban', function (require) {
    'use strict';

    var KanbanRecord = require('web.KanbanRecord');
    var KanbanRenderer = require('web.KanbanRenderer');
    var ColumnQuickCreate = require('web.kanban_column_quick_create');


    KanbanRenderer.include({
         _renderGrouped: function (fragment) {
        var self = this;

        // Render columns
        var KanbanColumn = this.config.KanbanColumn;
        _.each(this.state.data, function (group) {
            var column = new KanbanColumn(self, group, self.columnOptions, self.recordOptions);
            var def;
            if (group.value === "GR's without Gate" || group.value === "Anlieferungen ohne Gate") {
                console.log(column.get('$el'),"col");
                def = column.prependTo(fragment); // display the 'Undefined' group first
                self.widgets.unshift(column);
            } else {
                def = column.appendTo(fragment);
                self.widgets.push(column);
            }
            if (def.state() === 'pending') {
                self.defs.push(def);
            }

        });

        // remove previous sorting
        if(this.$el.sortable('instance') !== undefined) {
            this.$el.sortable('destroy');
        }
        if (this.groupedByM2O) {
            // Enable column sorting
            this.$el.sortable({
                axis: 'x',
                items: '> .o_kanban_group',
                handle: '.o_kanban_header_title',
                cursor: 'move',
                revert: 150,
                delay: 100,
                tolerance: 'pointer',
                forcePlaceholderSize: true,
                stop: function () {
                    var ids = [];
                    self.$('.o_kanban_group').each(function (index, u) {
                        // Ignore 'Undefined' column
                        if (_.isNumber($(u).data('id'))) {
                            ids.push($(u).data('id'));
                        }
                    });
                    self.trigger_up('resequence_columns', {ids: ids});
                },
            });

            // Enable column quickcreate
            if (this.createColumnEnabled) {
                this.quickCreate = new ColumnQuickCreate(this, {
                    examples: this.examples,
                });
                this.quickCreate.appendTo(fragment).then(function () {
                    // Open it directly if there is no column yet
                    if (!self.state.data.length) {
                        self.quickCreate.toggleFold();
                    }
                });

            }
        }
    },

    });

    KanbanRecord.include({
        /**
         * @override
         * @private
         */
        _onGlobalClick: function (event) {
            if ($(event.target).parents('.o_dropdown_kanban').length) {
                return;
            }
            var trigger = true;
            var elem = event.target;
            var ischild = true;
            var children = [];
            while (elem) {
                var events = $._data(elem, 'events');
                if (elem === event.currentTarget) {
                    ischild = false;
                }
                var test_event = events && events.click && (events.click.length > 1 || events.click[0].namespace !== 'bs.tooltip');
                var testLinkWithHref = elem.nodeName.toLowerCase() === 'a' && elem.href;
                if (ischild) {
                    children.push(elem);
                    if (test_event || testLinkWithHref) {
                        // Do not trigger global click if one child has a click
                        // event registered (or it is a link with href)
                        trigger = false;
                    }
                }
                if (trigger && test_event) {
                    _.each(events.click, function (click_event) {
                        if (click_event.selector) {
                            // For each parent of original target, check if a
                            // delegated click is bound to any previously found children
                            _.each(children, function (child) {
                                if ($(child).is(click_event.selector)) {
                                    trigger = false;
                                }
                            });
                        }
                    });
                }
                elem = elem.parentElement;
            }
            if (trigger) {

                var classes = this.el.classList;

                // Check if classList contains ignore_default_click_handler
                if (classes.contains('ignore_default_click_handler')) {

                    // This record is currently being dragged and dropped, so we do not
                    // want to open it.
                    if (this.$el.hasClass('o_currently_dragged')) {
                        return;
                    }

                    var editMode = this.$el.hasClass('oe_kanban_global_click_edit');

                    this.trigger_up('open_record', {
                        id: this.db_id,
                        mode: editMode ? 'edit' : 'readonly',
                    });

                } else {

                    this._openRecord();

                }

            }
        },

    });

});
