odoo.define("metro_dashboard.timeframe_dropdown_api", function(require) {

    $(document).ready(function() {
        const day30Btns = $(".metro_timeframe_30days")
        const day90Btns = $(".metro_timeframe_90days")

        for(let i = 0; i < day30Btns.length; i++) {
            const btn = $(day30Btns[i])

            btn.click(function() {
                let tile = $(this).parent().parent().parent().parent()

                let days30 = tile.find(".days30")
                let days90 = tile.find(".days90")
                let btn = tile.find("#timeframeDropdown")

                btn.html("<i class='fa fa-clock-o'></i> Last 30 days")

                for (let i = 0; i < days30.length; i++) {
                    $(days30[i]).attr("hidden", false)
                }
                for (let i = 0; i < days90.length; i++) {
                    $(days90[i]).attr("hidden", true)
                }
            })
        }

        for(let i = 0; i < day90Btns.length; i++) {
            const btn = $(day90Btns[i])

            btn.click(function() {
                let tile = $(this).parent().parent().parent().parent()

                let days30 = tile.find(".days30")
                let days90 = tile.find(".days90")
                let btn = tile.find("#timeframeDropdown")

                btn.html("<i class='fa fa-clock-o'></i> Last 90 days")

                for (let i = 0; i < days30.length; i++) {
                    $(days30[i]).attr("hidden", true)
                }
                for (let i = 0; i < days90.length; i++) {
                    $(days90[i]).attr("hidden", false)
                }
            })
        }
    })

})