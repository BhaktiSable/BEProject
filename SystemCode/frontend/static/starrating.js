$(document).ready(function() {
    var rating = parseFloat($('#star-rating').data('rating'));
    var percentage = (rating / 5) * 100;
    $('#star-rating').css('width', percentage + '%');
  });
  