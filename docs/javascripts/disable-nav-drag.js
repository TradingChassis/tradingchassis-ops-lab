document$.subscribe(() => {
    const links = document.querySelectorAll(
      ".md-sidebar--primary a, .md-sidebar--secondary a"
    );
  
    links.forEach(link => {
      link.setAttribute("draggable", "false");
      link.addEventListener("dragstart", event => {
        event.preventDefault();
      });
    });
  });