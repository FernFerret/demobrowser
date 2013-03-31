function deleteDemoRedirect(demoid, id, page, redirect){
    $.post(page, { demoid: demoid }, function(data) {
      window.location = redirect;
    });
}

function nukeDemo(demoid, id, page){
    $.post(page, { demoid: demoid }, function(data) {
        $(id).trigger('reveal:close');
        $('#demo'+demoid).fadeOut();
    });
}

var logFile;
var progress = document.getElementById('log_progress');

function sendFile(file) {
  $('#log_progress_ctr').fadeIn();
  progress.style.width = '0%';
  $('#log_progress_style').removeClass("progress-success").addClass("active").addClass("progress-striped").show();
  var xhr = new XMLHttpRequest();
  var fd = new FormData();

  xhr.open("POST", uri, true);
  xhr.upload.addEventListener("progress", function(e) {
    var pc = parseInt((e.loaded / e.total * 100));
    progress.style.width = pc + "%";
    if (pc == 100) {
      $('#log_progress_style').addClass("progress-success");
    }
  }, false);
  xhr.onreadystatechange = function() {
    // console.log(xhr);
    if (xhr.readyState == 4) {
      progress.style.width = "100%";
      $('#log_progress_style').removeClass("active").removeClass("progress-striped");
      setTimeout("$('#log_progress_ctr').fadeOut();", 2000);
      if (xhr.status == 200) {
        console.log(xhr.responseText);
        var obj = JSON.parse(xhr.responseText);
        console.log(obj);
        // Handle response.
        if (obj.success) {
          var msg = '<div class="alert alert-success"><a class="close" data-dismiss="alert">×</a>' + obj.msg + '</div>';
          $(msg).fadeIn().appendTo("#globalmsgs");
        } else {
          var msg = '<div class="alert alert-' + obj.cat + '"><a class="close" data-dismiss="alert">×</a>' + obj.msg + '</div>';
          $(msg).fadeIn().appendTo("#globalmsgs");
        }
      }
    }
  }
  fd.append('log_file', file);
  // Initiate a multipart/form-data upload
  xhr.send(fd);
}

function handleDragOver(evt) {
  evt.stopPropagation();
  evt.preventDefault();
  evt.dataTransfer.dropEffect = 'copy'; // Explicitly show this is a copy.
  $("#upload_overlay").show();
}

function handleFileSelect(evt) {
  evt.stopPropagation();
  evt.preventDefault();
  $("#upload_overlay").hide();
  $("#globalmsgs").children().each(function() {$(this).slideUp();});

  logFile = evt.dataTransfer.files[0]; // FileList object.

  // files is a FileList of File objects. List some properties.
  var output = [];
  var fn = escape(logFile.name);
  var name_match = fn.match(/^.*\.log$/);
  if (name_match == null) {
    var msg = '<div class="alert alert-danger"><a class="close" data-dismiss="alert">×</a><strong>ERROR: ' +
              '</strong>Only <code>.log</code> files accepted. You dropped this file: <code>' + fn + '</code></div>';
    $(msg).fadeIn().appendTo("#globalmsgs");
  } else {
    console.log(logFile);
    sendFile(logFile);
  }
}

function handleDragLeave(evt) {
  evt.stopPropagation();
  evt.preventDefault();
  // Get the location on screen of the element.
  var rect = this.getBoundingClientRect();

  // Check the mouseEvent coordinates are outside of the rectangle
  if(evt.x > rect.left + rect.width || evt.x < rect.left
  || evt.y > rect.top + rect.height || evt.y < rect.top) {
    $("#upload_overlay").hide();
    evt.dataTransfer.dropEffect = 'none';
  }
}

// Setup the dnd listeners.
var dropZone = document.getElementById('drop_zone');
dropZone.addEventListener('dragover', handleDragOver, false);
dropZone.addEventListener('dragleave', handleDragLeave, false);
dropZone.addEventListener('drop', handleFileSelect, false);