---
title: 詩歌選集 Selected Hymns
lang: en
# The project renders decks and pages; this one document is neither. How it
# looks is `_quarto.yml`'s business, as it is for both of those.
format: html
---

<form class="hymn-goto" id="hymn-goto" autocomplete="off">
  <label for="hymn-number">Hymn 詩歌</label>
  <input id="hymn-number" type="number" inputmode="numeric"
         min="1" max="{{< meta hymns >}}" step="1" placeholder="1"
         aria-describedby="hymn-goto-message" autofocus>
  <span class="hymn-goto-buttons">
    <button type="submit" value="slide">Slides 投影片</button>
    <button type="submit" value="hymn">Text &amp; scan 對照</button>
  </span>
  <span id="hymn-goto-message" class="hymn-goto-message" role="alert" hidden></span>
</form>

::: {.hymn-goto-explain}
[**Slides** project the hymn one stanza at a time, both languages, with the
chorus each stanza is sung with.]{lang=en}\
[**Text & scan** put the hymn beside the scanned page it was read off, to
follow the music or to check a line against the hymnal.]{lang=en}
:::
