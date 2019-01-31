Title: So, you want to copy some data?
Date: 2017-11-28 5:00
Modified: 2017-11-28 5:00
Category: Programming
Tags: mozilla, execcommand, web standards, clipboard
Slug: copying-text
Authors: Nika Layzell
Status: draft

If you want to have a button on your website which allows you to copy text to
the clipboard by clicking a button, the API which you will use to implement that
is `document.execCommand`. This is an old editor API, and because of that has
its fair share of browser specific quirks, and other issues.

The most common case for copying text to the clipboard is for copying small
amounts of text which are already in a textbox on the screen. For example, the
GitHub copy button would be implemented like this:

```html
<input type="text" id="ex1" value="https://github.com/mystor/mystor.github.io/" readonly>
<button id="ex1-btn">Copy</button>
<script>
  document.querySelector("#ex1-btn").addEventListener("click", function() {
    document.querySelector("#ex1").select();
    document.execCommand("copy");
  });
</script>
```

<div style="text-align: center;">
<input type="text" id="ex1" value="https://github.com/mystor/mystor.github.io/" readonly>
<button id="ex1-btn">Copy</button>
<script>
  document.querySelector("#ex1-btn").addEventListener("click", function() {
    document.querySelector("#ex1").select();
    document.execCommand("copy");
  });
</script>
</div>

This code selects the text of an existing textbox. For short strings like
GitHub's URLs, this is a perfectly fine solution. It's simple, portable, and
selecting a short string like that is really fast.

However, people also want to use the clipboard for copying around much larger
amounts of data. For example, some sites provide the ability to export SVGs or
other large pieces of data to the clipboard. In these cases, adding a text area
to the DOM dynamically, and selecting it, can be very slow. For example consider
the following code:

```html
<button id="ex2-btn">Copy 8Mb of Data (naive)</button>
<script>
  document.querySelector("#ex2-btn").addEventListener("click", function() {
    var data = getData();

    let textarea = createAndSelectDummyTextArea(data);
    document.execCommand("copy");
    textarea.parentNode.removeChild(textarea);
  });
</script>
```

> **WARNING** Clicking this button _may_ hang your browser for a couple of seconds. 
> 
> In my testing Firefox 57 manages to avoid laying out the textbox if it is
> marked as readonly, as we remove it before the next vsync, but Chrome 62 hangs
> reflowing during text selection.

<div style="text-align: center;">
<button id="ex2-btn">Copy 8Mb of Data (naive)</button>
<script>
  document.querySelector("#ex2-btn").addEventListener("click", function() {
    var data = getData();

    let textarea = createAndSelectDummyTextArea(data);
    document.execCommand("copy");
    textarea.parentNode.removeChild(textarea);
  });
</script>
</div>

On some browsers, the above code triggers a very expensive synchronous reflow
when selecting the text in the offscreen textarea, which can last for multiple
seconds. This isn't great for text copying performance. It would be much nicer
if we could copy text to the clipboard without needing to put it in a textarea!

This is possible through the use of the `copy` clipboard event. This event is
fired on the document when a copy is performed, and is given access to
a [`DataTransfer`] [1], which can be used to directly modify the data to be
copied to the clipboard.

```html
<button id="ex3-btn">Copy 8Mb of Data (FF & Chrome)</button>
<script>
  document.querySelector("#ex3-btn").addEventListener("click", function() {
    var data = getData();
    
    function handler(evt) {
      evt.clipboardData.setData("text/plain", data);
      evt.preventDefault();
    }

    document.addEventListener("copy", handler);
    document.execCommand("copy");
    document.removeEventListener("copy", handler);
  });
</script>
```

> **NOTE** As of the time of writing this post, this button will only work on
> Firefox and Chrome. We'll make it work on more browsers next.

<div style="text-align: center;">
<button id="ex3-btn">Copy 8Mb of Data (FF & Chrome)</button>
<script>
  document.querySelector("#ex3-btn").addEventListener("click", function() {
    var data = getData();
    
    function handler(evt) {
      evt.clipboardData.setData("text/plain", data);
      evt.preventDefault();
    }

    document.addEventListener("copy", handler);
    document.execCommand("copy");
    document.removeEventListener("copy", handler);
  });
</script>
</div>

Unfortunately, this will only work on Firefox and Chrome. Internet Explorer,
Edge, and Safari don't fully implement the standard, and require a valid copy
selection to perform a `document.execCommand("copy")`, even if a copy event
handler is registered, so we can create a small offscreen text box with a
selection for that purpose. In addition, Internet Explorer doesn't expose
`clipboardData` as a member of the event, and requires a non-standard MIME type,
so we need to handle that too:

```html
<button id="ex4-btn">Copy 8Mb of Data (portable)</button>
<script>
  document.querySelector("#ex4-btn").addEventListener("click", function() {
    var data = getData();
    
    function handler(evt) {
      if (typeof evt.clipboardData !== "undefined") {
        evt.clipboardData.setData("text/plain", data);
      } else {
        // Handle IE's non-standard clipboardData API.
        clipboardData.setData("TEXT", data);
      }
      evt.preventDefault();
    }

    // The dummy textarea is required for Safari and IE/Edge.
    var textarea = createAndSelectDummyTextArea("_");
    document.addEventListener("copy", handler);
    document.execCommand("copy");
    document.removeEventListener("copy", handler);
    textarea.parentNode.removeChild(textarea);
  });
</script>
```

<div style="text-align: center;">
<button id="ex4-btn">Copy 8Mb of Data (portable)</button>
<script>
  document.querySelector("#ex4-btn").addEventListener("click", function() {
    var data = getData();
    
    function handler(evt) {
      if (typeof evt.clipboardData !== "undefined") {
        evt.clipboardData.setData("text/plain", data);
      } else {
        // Handle IE's non-standard clipboardData API.
        clipboardData.setData("TEXT", data);
      }
      evt.preventDefault();
    }

    // The dummy textarea is required for Safari and IE/Edge.
    var textarea = createAndSelectDummyTextArea("_");
    document.addEventListener("copy", handler);
    document.execCommand("copy");
    document.removeEventListener("copy", handler);
    textarea.parentNode.removeChild(textarea);
  });
</script>
</div>

Unfortunately popular clipboard libraries like [clipboard.js] [2], are focused
on the small text copy usecase, and don't do this work for you. If you want a
small library which just copies text with no fancy features, I've
written [raw_copy] [3].

> **NOTE** I have previously submitted a PR to clipboard.js to improve the speed
> of copying large amounts of data ([#412] [4]), and it was rejected due to the
> additional complexity required to implement this with the clipboard.js API.
> 
> This was a reasonable decision, but it makes the library a poor choice for
> developers who need to copy megabytes of data.

[1]: https://developer.mozilla.org/en-US/docs/Web/API/DataTransfer "DataTransfer"
[2]: https://clipboardjs.com/ "clipboard.js"
[3]: https://github.com/mystor/raw_copy "raw_copy"
[4]: https://github.com/zenorocha/clipboard.js/pull/412 "zenorocha/clipboard.js#412"

<hr>

The following is the implementation of the helper functions used in the above
examples - They were factored out to keep the code clear.

```js
function getData() {
  // 8Mb (2^23 bytes) of "a"s should be enough.
  var data = "a";
  for (var i = 0; i < 23; ++i) { data += data; }
  return data;
}

function createAndSelectDummyTextArea(text) {
  var dummy = document.createElement("textarea");

  // Move the element out of screen horizontally.
  dummy.style.position = "absolute";
  dummy.style.left = "-9999px";

  // Ensure we don't have to scroll to select the text.
  var scrolltop = window.pageYOffset || document.documentElement.scrollTop;
  dummy.style.top = scrolltop + "px";
  
  // On some browsers readonly textboxes are faster.
  dummy.setAttribute("readonly", "");

  // Add the element to the document.
  dummy.value = text;
  document.body.appendChild(dummy);

  // Select the textarea.
  dummy.select();

  return dummy;
}
```

<script>
  function getData() {
    // 8Mb (2^23 bytes) of "a"s should be enough.
    var data = "a";
    for (var i = 0; i < 23; ++i) { data += data; }
    return data;
  }

  function createAndSelectDummyTextArea(text) {
    var dummy = document.createElement("textarea");

    // Move the element out of screen horizontally.
    dummy.style.position = "absolute";
    dummy.style.left = "-9999px";

    // Ensure we don't have to scroll to select the text.
    var scrolltop = window.pageYOffset || document.documentElement.scrollTop;
    dummy.style.top = scrolltop + "px";
    
    // On some browsers readonly textboxes are faster.
    dummy.setAttribute("readonly", "");

    // Add the element to the document.
    dummy.value = text;
    document.body.appendChild(dummy);

    // Select the textarea.
    dummy.select();

    return dummy;
  }
</script>
