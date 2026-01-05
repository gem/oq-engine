function capitalizeFirstLetter(val) {
    return String(val).charAt(0).toUpperCase() + String(val).slice(1);
}

function showConfirmationModal({ id, title, body, confirmText = 'Yes', cancelText = 'No', confirmAction }) {
  const modal = document.querySelector('#confirmModal');
  modal.querySelector('.modal-title').innerHTML = title;
  modal.querySelector('.modal-body-pre').innerHTML = body;
  modal.querySelector('.btn-confirm').textContent = confirmText;
  modal.querySelector('.btn-cancel').textContent = cancelText;

  // Attach confirmation action
  const confirmButton = modal.querySelector('.btn-confirm');
  confirmButton.onclick = () => {
    if (typeof confirmAction === 'function') {
      confirmAction();
    }
    closeModal();
  };

  // Show the modal
  modal.classList.remove('hide');
  modal.classList.add('in');
}

function closeModal() {
  const modal = document.querySelector('#confirmModal');
  modal.classList.remove('in');
  modal.classList.add('hide');
}

function showNotificationModal(title, message) {
    $("#genericModalTitle").text(title);
    $("#genericModalBody").html(message);   // can accept HTML
    $("#genericModal").modal("show");
}

var progressHandlingFunction = function (progress) {
    var percent = progress.loaded / progress.total * 100;
    $('.bar').css('width', percent + '%');
    if (percent == 100) {
        dialog.hide();
    }
};

var htmlEscape = function (record) {
    // record[3] is the log message
    record[3] = record[3].replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return record
};

var dialog = (function () {
    var pleaseWaitDiv = $('<div class="modal hide" id="pleaseWaitDialog" data-backdrop="static" data-keyboard="false"><div class="modal-header"><h1>Processing...</h1></div><div class="modal-body"><div class="progress progress-striped active"><div class="bar" style="width: 0%;"></div></div></div></div>');
    return {
        show: function (msg, progress) {
            $('h1', pleaseWaitDiv).text(msg);
            if (progress) {
                progressHandlingFunction({loaded: 0, total: 1});
            } else {
                progressHandlingFunction({loaded: 1, total: 1});
            }
            pleaseWaitDiv.modal('show');
        },
        hide: function () {
            pleaseWaitDiv.modal('hide');
        }
    };
})();

var diaerror = (function () {
    var errorDiv = $('<div id="errorDialog" class="modal hide" data-keyboard="true" tabindex="-1">\
            <div class="modal-dialog">\
              <div class="modal-content">\
                <div class="modal-header">\
                  <h4 class="modal-title">Calculation not accepted: traceback</h4>\
                </div>\
                <div class="modal-body" style="font-size: 12px;"><pre style="font-size: 12px;" class="modal-body-pre"></pre>\
                </div>\
                <div class="modal-footer">\
                  <span id="diaerror_scroll_enabled_box" style="display: none;"><input type="checkbox" id="diaerror_scroll_enabled" checked>\
                  Auto Scroll</span>&nbsp;&nbsp;&nbsp;\
                  <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>\
                </div>\
              </div>\
            </div>\
        </div>');
    errorDiv.bind('hide', function () {
        $(document).trigger('errorDialog:hidden');
    });
    return {
        getdiv: function () {
            return errorDiv;
        },

        show: function (is_large, title, msg) {
            if (title != null) {
                $('.modal-title', errorDiv).html(title);
            }
            if (msg != null) {
                $('.modal-body-pre', errorDiv).html(msg);
            }
            if (is_large) {
                errorDiv.addClass("errorDialogLarge");
            }
            else {
                errorDiv.removeClass("errorDialogLarge");
            }
            errorDiv.modal('show');
        },

        append: function (title, msg) {
            if (title != null) {
                $('.modal-title', errorDiv).html(title);
            }
            $( msg ).appendTo( $('.modal-body-pre', errorDiv) );
        },

        scroll_to_bottom: function (ctx) {
            ctx.scrollTop(ctx[0].scrollHeight);
        },

        hide: function () {
            errorDiv.modal('hide');
        }
    };
})();
