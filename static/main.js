$('#letters').submit(function(e) {
    var data = $('#letters').serialize();


    $.ajax({
        type: "POST",
        url: '',
        data: data,
        success: function(data) {
            if (data.finished) {
                location.reload();
            }
            else {
                $('#current').text(data.current);

                $('#mistakes').html('Mistakes: ' + data.mistakes.length + '/6');
                console.log(data);
                updateHangman(data.mistakes.length);
            }

        }
    });
    e.preventDefault();

});

function updateHangman(mistakeslength){
    $("#hang").children().slice(0, mistakeslength).show();

}
