(function () {
  var params = new URLSearchParams(window.location.search);
  var root = document.getElementById("app");
  globalThis.__flowlight = FlowlightEngine.mount(root, {
    initialDemo: params.get("demo") === "1",
    initialLive: params.get("live") === "1",
    autoselect: params.get("select") || "",
    invoicePhase: params.get("phase") || "",
    pollMs: 8000,
    poll: function (query) {
      var search = new URLSearchParams();
      if (query && query.demo) search.set("demo", "1");
      if (query && query.live) search.set("live", "1");
      if (query && query.phase) search.set("phase", query.phase);
      return fetch("/api/graph?" + search.toString(), { headers: { Accept: "application/json" } }).then(function (response) {
        if (!response.ok) throw new Error("graph " + response.status);
        return response.json();
      });
    }
  });
}());
