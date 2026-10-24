function addInline(el, text) {
  const tokens = text.split(/(\*\*[^*]+?\*\*|\*[^*\n]+?\*)/);
  for (const tok of tokens) {
    if (!tok) continue;
    if (tok.startsWith("**") && tok.endsWith("**") && tok.length > 4) {
      const s = document.createElement("strong");
      s.textContent = tok.slice(2, -2).replace(/\*/g, "").trim();
      el.append(s);
    } else if (tok.startsWith("*") && tok.endsWith("*") && tok.length > 2) {
      const e = document.createElement("em");
      e.textContent = tok.slice(1, -1).replace(/\*/g, "").trim();
      el.append(e);
    } else {
      const clean = tok.replace(/\*/g, "");
      if (clean) el.append(document.createTextNode(clean));
    }
  }
}

function renderText(container, text) {
  let ul = null;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line || /^[-*_\s]+$/.test(line)) { ul = null; continue; }

    const bullet = line.match(/^[-*]\s+(.*)$/);
    if (bullet) {
      const content = bullet[1].replace(/^\*+|\*+$/g, "").trim();
      if (!content) continue;
      if (!ul) { ul = document.createElement("ul"); container.append(ul); }
      const li = document.createElement("li");
      addInline(li, content);
      ul.append(li);
      continue;
    }

    ul = null;
    const heading = line.match(/^#{1,6}\s+(.*)$/);
    const el = document.createElement(heading ? "h4" : "p");
    addInline(el, heading ? heading[1] : line);
    if (el.textContent.trim()) container.append(el);
  }
}
