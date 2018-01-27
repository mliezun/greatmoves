$(document).ready(function () {
    var last_post_id = $('#last-post-id').html()
    var turns = [true]
    $(window).bind('scroll', function() {
      var scrollTop = $(window).scrollTop()
      var maxScroll = $(document).height() - $(window).height()
      var turn = turns.pop()
      if (turn) {
        if (scrollTop/maxScroll > 0.8) {
          $.ajax({
            url: '/more_posts/' + last_post_id,
            success: function (result) {
              if (result === '') {
                $(window).unbind('scroll')
              } else {
                last_post_id = ''
                for (var i = result.length-1; i >= 0; i--) {
                  if (result[i] === '#') break
                  last_post_id = result[i] + last_post_id
                }
                result = result.substring(0, i)
                var posts = $('#posts').html()
                $('#posts').html(posts + result)
                turns.push(true)
              }
            }
          })
        }
        else {
          turns.push(true)
        }
      }

   })

   $(window).scroll()
})
