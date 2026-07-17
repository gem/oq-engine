function selectTextareaLine(textarea, lineNum) {
    // Taken from http://stackoverflow.com/questions/13650534/how-to-select-line-of-text-in-textarea
    lineNum--; // array starts at 0
    var lines = textarea.value.split("\n");

    // calculate start/end
    var startPos = 0, endPos = textarea.value.length;
    for(var x = 0; x < lines.length; x++) {
        if(x == lineNum) {
            break;
        }
        startPos += (lines[x].length+1);

    }

    var endPos = lines[lineNum].length+startPos;

    // do selection
    // Chrome / Firefox

    if(typeof(textarea.selectionStart) != "undefined") {
        textarea.focus();
        textarea.selectionStart = startPos;
        textarea.selectionEnd = endPos;
        return true;
    }

    // IE
    if (document.selection && document.selection.createRange) {
        textarea.focus();
        textarea.select();
        var range = document.selection.createRange();
        range.collapse(true);
        range.moveEnd("character", endPos);
        range.moveStart("character", startPos);
        range.select();
        return true;
    }

    return false;
}



