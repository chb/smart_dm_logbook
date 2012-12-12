'use strict';

// simplified module definition: no filters, services, or directives
// and only one view without a parital. It's also configured with
// alternate interpolation delimiters as to not conflict with Django
angular.module('App', ['App.directives'])
  .config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/view1')
    $routeProvider.otherwise({redirectTo: '/view1'});
  }])
  .config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('{[{');
    $interpolateProvider.endSymbol('}]}');
  });
