function editDemo(demoid, id, loading){
    $.get('demos/edit/'+demoid, function(data) {
      $(id).html(data);
      $(loading).hide();
    });
}

function viewDemo(demoid, id, loading){
    $.get('demos/view/'+demoid, function(data) {
      $(id).html(data);
      $(loading).hide();
    });
}