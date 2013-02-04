'use strict';

var FLOAT_REGEXP = /^\-?\d+((\.|\,)\d+)?$/;

angular.module('App.directives', [])
  .directive('smartFloat', function() {
    return {
      require: 'ngModel',
      link: function(scope, elm, attrs, ctrl) {
        ctrl.$parsers.unshift(function(viewValue) {
          if (FLOAT_REGEXP.test(viewValue)) {
            ctrl.$setValidity('float', true);
            return parseFloat(viewValue.replace(',', '.'));
          } else {
            ctrl.$setValidity('float', false);
            return undefined;
          }
        });
      }
    };
  })
  // based on the mbostock's scatterplot http://bl.ocks.org/3887118
  .directive('glucoseDay', function() {
    return {
      restrict: 'E',
      terminal: true,
      scope: { val: '=' },
      link: function (scope, element, attrs) {
        function getDate(d) { return new Date(d); }
        function getHour(d) {
          var x = new Date(d)
          // dates are in UTC, translate to local time
          return x.getHours() + x.getTimezoneOffset() / 60;
        }

        var margin = {top: 20, right: 20, bottom: 30, left: 40},
            width = 960 - margin.left - margin.right,
            height = 500 - margin.top - margin.bottom;

        var x = d3.scale.linear().domain([0, 24]).range([0, width]).nice();

        var y = d3.scale.linear().range([height, 0]);

        var color = d3.scale.category10();

        var xAxis = d3.svg.axis().scale(x).orient("bottom");
        var yAxis = d3.svg.axis().scale(y).orient("left");

        var svg = d3.select(element[0]).append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
          .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        // angular listener
        scope.$watch('val', function(newVal, oldVal) {
          if (!newVal) { return; }
          svg.selectAll('*').remove();

          // set the y domain after we have the data to auto scale
          y.domain([0, d3.max(newVal, function(d) { return d.value; })]).nice();

          svg.append("g")
              .attr("class", "x axis")
              .attr("transform", "translate(0," + height + ")")
              .call(xAxis)
            .append("text")
              .attr("class", "label")
              .attr("x", width)
              .attr("y", -6)
              .style("text-anchor", "end")
              .text("Time of day");

          svg.append("g")
                  .attr("class", "y axis")
                  .call(yAxis)
                .append("text")
                  .attr("class", "label")
                  .attr("transform", "rotate(-90)")
                  .attr("y", 6)
                  .attr("dy", ".71em")
                  .style("text-anchor", "end")
                  .text("Glucose (mmol/L)")

            svg.selectAll(".dot")
                .data(newVal)
              .enter().append("circle")
                .attr("class", "dot")
                .attr("r", 5)
                .attr("cx", function(d) { return x(getHour(d.when)); })
                .attr("cy", function(d) { return y(d.value); })
                .style("fill", function(d) { return color(); });
        });
      }
    }
  })
  // based on http://bl.ocks.org/3885304
  .directive('glucoseHistogram', function() {
    return {
      restrict: 'E',
      terminal: true,
      scope: { val: '=' },
      link: function (scope, element, attrs) {
        var margin = {top: 20, right: 20, bottom: 30, left: 40},
            width = 960 - margin.left - margin.right,
            height = 500 - margin.top - margin.bottom;

        // create a custom x domain from 3 to 15
        var x_domain = [];
        for (var i = 3; i < 16; i += 1) { x_domain.push(i); }
        var x = d3.scale.quantize().domain(x_domain).range(x_domain);
        var y = d3.scale.linear().range([height, 0]);
        var color = d3.scale.category10();
        var yAxis = d3.svg.axis().scale(y).orient("left");

        // the x_scale has a domain of 3 to 15 (n = 12) and a range of width - margins (900)
        var x_scale = d3.scale.linear().domain([3,15]).range([0, 900]);
        var xAxis = d3.svg.axis().scale(x_scale).orient("bottom").tickValues(x_domain);

        var svg = d3.select(element[0]).append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        // angular listener
        scope.$watch('val', function(newVal, oldVal) {
          if (!newVal) { return; }
          svg.selectAll('*').remove();

          // round values
          var rounded = _.map(newVal, function(v) { return Math.round(v.value); });
          rounded = _.sortBy(rounded, function(v) { return v; });

          // generate counts based on rounded values
          var counts = [];

          rounded.forEach(function(d) {
            var found = false;
            for (var i = 0; i < counts.length; i += 1) {
              if (counts[i][0] === d) {
                counts[i][1] = counts[i][1] + 1;
                found = true;
              }
            }
            if (!found) { counts.push([d, 1]); }
          });

          //console.log(counts);

          // set the y domain after we have the data to auto scale
          y.domain([0, d3.max(counts, function(d) { return d[1]; })]).nice();
          // use the domain to set the ticks
          var y_ticks = _.range(0, y.domain()[1]+1);
          //console.log(y_ticks);
          var yAxis = d3.svg.axis().scale(y).orient("left").tickValues(y_ticks).tickFormat(d3.format("0d"));

          svg.append("g")
               .attr("class", "x axis")
               .attr("transform", "translate(0," + height + ")")
               .call(xAxis)
             .append("text")
               .attr("class", "label")
               .attr("x", width)
               .attr("y", -6)
               .style("text-anchor", "end")
               .text("Glucose (mmol/L)");

          svg.append("g")
               .attr("class", "y axis")
               .call(yAxis)
             .append("text")
               .attr("class", "label")
               .attr("transform", "rotate(-90)")
               .attr("y", 6)
               .attr("dy", ".71em")
               .style("text-anchor", "end")
               .text("Number of Measurements")

            svg.selectAll(".bar")
               .data(counts)
               .enter()
               .append("rect")
               .attr("class", "bar")
               .attr("width", 75)
               .attr("x", function(d) {
                 var a = d[0];
                 // x value * bar width - (x value of 3.5 + half bar width)
                 var b = x(a) * 75 - (225 + 37.5)
                 //console.log(a, x(a), b);
                 return b;
               })
               .attr("y", function(d) { return y(d[1]); })
               .attr("height", function(d) { return height - y(d[1]); });
        });
      }
    }
  })
