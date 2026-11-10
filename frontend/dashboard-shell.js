(function () {
  "use strict";
  var SDK = window.__HERMES_PLUGIN_SDK__;
  if (!SDK || !SDK.React || !window.__HERMES_PLUGINS__) return;
  var React = SDK.React;
  var h = React.createElement;

  /*__ENGINE__*/

  function Page() {
    var ref = React.useRef(null);
    React.useEffect(function () {
      var node = ref.current;
      if (!node) return undefined;
      var handle = mountFlowlight(node, {
        pollMs: 8000,
        poll: function (query) {
          var search = new URLSearchParams();
          if (query && query.demo) search.set("demo", "1");
          if (query && query.live) search.set("live", "1");
          if (query && query.phase) search.set("phase", query.phase);
          return fetch("/api/plugins/flowlight/graph?" + search.toString(), {
            credentials: "same-origin",
            headers: { Accept: "application/json" }
          }).then(function (response) {
            if (!response.ok) throw new Error("graph " + response.status);
            return response.json();
          });
        }
      });
      return function () { handle.destroy(); };
    }, []);
    return h("div", {
      ref: ref,
      className: "flowlight-dash",
      style: { height: "calc(100vh - 96px)", minHeight: "560px" }
    });
  }

  window.__HERMES_PLUGINS__.register("flowlight", Page);
}());
