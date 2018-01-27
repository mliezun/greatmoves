$(document).ready(function () {
    $(window).bind('scroll', function() {
      var scrollTop = $(window).scrollTop()
      var maxScroll = $(document).height() - $(window).height()
      if (scrollTop/maxScroll > 0.8) {
        $.get('/more_posts/' + window.last_post_id, function (result) {
          if (result === '') {
            $(window).unbind('scroll')
          } else {  
            var content = $('#content').html()
            $('#content').html(content + result)
          }
        })
      }
   })
   $(window).scroll()
})
