(function() {
    var docHeight = $(window).height();
    var footerHeight = $('#footer').height();
    var footerTop = $('#footer').position().top + footerHeight;

    if (footerTop < docHeight) {
        $('#footer').css('margin-top', (docHeight - footerTop) + 'px');
    }

    $('.post-body').each(function (i, e) {
        $(e).shorten({
            showChars: 500,
            moreText: 'read more'
        })
    })
})()
