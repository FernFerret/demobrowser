function viewDemo(demoid, id, loading, page){
    $.get(page, function(data) {
      $(id).html(data);
      $(loading).hide();
    });
}

function deleteDemo(demoid, id, page){
    $.post(page, { demoid: demoid }, function(data) {
        $(id).trigger('reveal:close');
        $('#demo'+demoid).fadeOut();
    });
}
