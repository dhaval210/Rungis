odoo.define("metro_dashboard.ChartBase", function(require) {
    "use strict"

    function ChartBase(data) {
        this.init = function(data) {
            this.result = JSON.parse(data["result"])
            
            this.name = data["name"]
            this.type = data["visualisation"]
            this.suffix = data["suffix"] || ""
            this.keys = data["keys"]
            this.canvas = data["canvas"]
            this.dataSource = data["data_source"]

            this.datasets = []

            this.initCalled = true

            return this
        },
        this.generateChart = function() {
            if (!this.initCalled) {
                console.error("Init function of ChartBase not called before calling generateChart()\nMake sure you call init first")
                return
            }

            if (this.result instanceof Object && this.result.constructor === Array) {
                // Multiple Datasets are provided
                let name

                if (this.result.length >= 2) {
                    for (let index in this.result) {
                        const res = this.result[index]
                        if (typeof(res) === "string") {
                            name = res;
                        } else {
                            // Generate background and border colors
                            // Make sure the values are retrieved in the same order
                            // as the keys
                            const data = this.keys.map((key) => res[key]);
                            const [backgroundColor, borderColor] = this._generateColors(data);

                            const dataset = {
                                label: name,
                                backgroundColor: this.type == "line" ? "rgb(0,0,0,0)" : backgroundColor,
                                borderColor: borderColor,
                                data: data
                            }
                            this.datasets.push(dataset);
                        }
                    }
                } else {
                    console.error("The result for %s needs to contain at least 2 values. One for the label of the dataset and the dataset itself.", this.name);
                }
            } else {
                if (this.keys.length >= 1) {
                    const data = this.keys.map((key) => this.result[key]);
                    const [backgroundColor, borderColor] = this._generateColors(data);

                    const dataset = {
                        label: this.name,
                        backgroundColor: backgroundColor,
                        borderColor: borderColor,
                        data: data
                    }
                    this.datasets.push(dataset);
                } else {
                    console.warn("The result for %s is not present.", this.name)
                }
            }

            let xAxes = [{
                display: this.type == "pie" ? false : true
            }];
            let yAxes = [{
                ticks: {
                    beginAtZero: true,
                    display: this.type == "pie" ? false : true
                },
                gridLines: {
                    drawBorder: this.type == "pie" ? false : true,
                    display: this.type == "pie" ? false : true
                }
            }];

            if (this.datasets.length > 1 && this.type == "bar") {
                xAxes[0]["stacked"] = true;
                yAxes[0]["stacked"] = true;
            }

            const self = this

            // Building Chart with the ChartJS Framework
            const chart = new Chart(this.canvas, {
                // Setting type, e.g. "bar" or "line"
                type: this.type,
                data: {
                    // Setting labels for x Axis
                    labels: this.keys,
                    datasets: this.datasets
                },
                // Begin at zero
                // Otherwise it would begin at the minimum value
                options: {
                    scales: {
                        xAxes: xAxes,
                        yAxes: yAxes
                    },
                    // Format the tooltips for the graph to display the correct values
                    tooltips: {
                        enabled: true,
                        mode: "nearest",
                        callbacks: {
                            title: function(item, chartData) {
                                let name = self.keys[item[0].index];
                                return name;
                            },
                            label: function(item, chartData) {
                                let suffix = ""
                                if (self.dataSource == "python") {
                                    suffix = self.suffix
                                } else if (self.dataSource == "data") {
                                    let temp = JSON.parse(self.suffix)
                                    suffix = temp[chartData.datasets[item.datasetIndex].label] || ""
                                }
                                let value = chartData.datasets[item.datasetIndex].data[item.index];
                                value = Math.round(value*100)/100;
                                return value + " " + suffix;
                            }
                        }
                    }
                }
            });

            return chart
        },
        this._preventWhite = function(red, green, blue) {
            let r = red, g = green, b = blue;
            
            // Randomize which color gets reduced
            if(r > 200 && g > 200 && b > 200) {
                const i = Math.floor(Math.random()*3);
                if (i == 0) r -= 50;
                else if (i == 1) g -= 50;
                else b -= 50;
            }

            return [r, g, b];
        },
        this._preventSimilarColors = function(rgb1, rgb2) {
            let new1 = rgb1;
            let new2 = rgb2;
            
            const positiveNum = (num) => {if (num < 0) return num * -1; else return num;}
            const red_diff = rgb1[0] - rgb2[0];
            const green_diff = rgb1[1] - rgb2[1];
            const blue_diff = rgb1[2] - rgb2[2];
            
            if (positiveNum(red_diff) < 80 && positiveNum(green_diff) < 80 && positiveNum(blue_diff) < 80) {
                const i = Math.floor(Math.random() * 3);
                const op = Math.floor(Math.random() * 2);
                let amount = Math.floor(Math.random() * 100);
                amount = amount < 50 ? amount += 50 : amount;

                if (op == 0) {
                    new1[i] = new1[i] + Number.parseInt(amount / (i == 0 ? 1 : i));
                    new2[i] = positiveNum(new2[i] - amount);

                    if (new1 > 255) {
                        new1[i] -= 255;
                    }
                } else {
                    new1[i] = positiveNum(new1[i] - Number.parseInt(amount / (i == 0 ? 1 : i)));
                    new2[i] = new2[i] + amount;
                    if (new2 > 255) {
                        new2[i] -= 255;
                    }
                }

                [new1, new2] = this._preventSimilarColors(new1, new2);
            }

            return [new1, new2];
        },
        this._generateColors = function(data) {
            // Variables for randomizing colors
            let backgroundColor = "rgba(0,0,0,0)", borderColor = "rgba(0,0,0,0)";

            // Randomize colors, different color types are needed for
            // Bar and Line charts
            if(this.type == "line") {
                let r = Math.floor(Math.random()*256);
                let g = Math.floor(Math.random()*256);
                let b = Math.floor(Math.random()*256);

                [r, g, b] = this._preventWhite(r, g, b);
                
                borderColor = "rgb("+r+","+g+","+b+")";
                backgroundColor = "rgba("+r+","+g+","+b+", 0.3)";
            } else if (this.type == "bar") {
                let r = Math.floor(Math.random()*256);
                let g = Math.floor(Math.random()*256);
                let b = Math.floor(Math.random()*256);

                [r, g, b] = this._preventWhite(r, g, b);

                backgroundColor = "rgb("+r+","+g+","+b+")";
            } else {
                // Pie Charts need to have a different color for every piece of data
                backgroundColor = []
                borderColor = []
                let last_rgbs = [];
                for(let i = 0; i < data.length; i++) {
                    let r = Math.floor(Math.random()*256);
                    let g = Math.floor(Math.random()*256);
                    let b = Math.floor(Math.random()*256);

                    [r, g, b] = this._preventWhite(r, g, b);
                    
                    let curr_rgb = [r, g, b];

                    for (let x = 1; x <= last_rgbs.length; x++) {
                        let last = last_rgbs[x - 1];

                        let [rgb1, rgb2] = this._preventSimilarColors(last, curr_rgb);
                        [r, g, b] = rgb2;
                        last_rgbs[x - 1] = rgb1;
                    }

                    last_rgbs.push([r, g, b]);
                }
                for(let index in last_rgbs) {
                    const rgb = last_rgbs[index];
                    const color = "rgb("+rgb[0]+","+rgb[1]+","+rgb[2]+")";
                    backgroundColor.push(color);
                }
            }

            return [backgroundColor, borderColor];
        }

        this.init(data)
    }

    return ChartBase
})