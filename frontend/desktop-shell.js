import { useEffect, useRef, useState } from "react";
import { jsx } from "react/jsx-runtime";
import { PALETTE_AREA, ROUTES_AREA, SIDEBAR_NAV_AREA, STATUSBAR_AREAS, host } from "@hermes/plugin-sdk";

/*__ENGINE__*/

function flowQuery(extra) {
  var demo = extra && extra.demo ? "1" : "0";
  var live = extra && extra.live ? "1" : "0";
  return "/graph?demo=" + demo + "&live=" + live;
}

function FlowStage(props) {
  var ctx = props.ctx;
  var ref = useRef(null);
  useEffect(function () {
    var node = ref.current;
    if (!node) return undefined;
    var handle = mountFlowlight(node, {
      pollMs: 8000,
      setInterval: function (fn, ms) { return ctx.setInterval ? ctx.setInterval(fn, ms) : setInterval(fn, ms); },
      clearInterval: function (id) { return ctx.clearInterval ? ctx.clearInterval(id) : clearInterval(id); },
      poll: function (query) {
        return ctx.rest(flowQuery(query));
      }
    });
    var stop = function () { handle.destroy(); };
    if (ctx.onDispose) ctx.onDispose(stop);
    return stop;
  }, [ctx]);
  return jsx("div", { ref: ref, style: { height: "100%", minHeight: "320px", width: "100%" } });
}

function FlowStatus(props) {
  var ctx = props.ctx;
  var pair = useState("Flowlight");
  var label = pair[0];
  var setLabel = pair[1];
  useEffect(function () {
    var alive = true;
    function pull() {
      ctx.rest("/summary").then(function (body) {
        if (!alive || !body) return;
        var summary = body.summary || {};
        var count = summary.count || 0;
        var mode = body.demo ? "demo" : "live";
        setLabel(count ? "Flowlight " + count + " · " + mode : "Flowlight · " + mode);
      }).catch(function () {
        if (alive) setLabel("Flowlight");
      });
    }
    pull();
    var timer = ctx.setInterval ? ctx.setInterval(pull, 20000) : setInterval(pull, 20000);
    return function () {
      alive = false;
      if (ctx.clearInterval) ctx.clearInterval(timer);
      else clearInterval(timer);
    };
  }, [ctx]);
  return jsx("button", {
    type: "button",
    onClick: function () { host.navigate("/flowlight"); },
    style: {
      border: "none",
      background: "transparent",
      color: "inherit",
      font: "inherit",
      cursor: "pointer",
      padding: "0 6px"
    },
    children: label
  });
}

export default {
  id: "flowlight",
  name: "Flowlight",
  register: function (ctx) {
    ctx.register({
      id: "pane",
      area: "panes",
      title: "Flowlight",
      data: { placement: "right", dock: { pane: "workspace", pos: "right" }, width: "440px" },
      render: function () { return jsx(FlowStage, { ctx: ctx }); }
    });
    ctx.registerMany([
      {
        id: "page",
        area: ROUTES_AREA,
        data: { path: "/flowlight" },
        render: function () { return jsx(FlowStage, { ctx: ctx }); }
      },
      {
        id: "nav",
        area: SIDEBAR_NAV_AREA,
        data: { path: "/flowlight", label: "Flowlight", codicon: "pulse" }
      },
      {
        id: "open",
        area: PALETTE_AREA,
        data: {
          id: "flowlight.open",
          label: "Open Flowlight",
          keywords: ["flows", "wallet", "onchain"],
          run: function () { host.navigate("/flowlight"); }
        }
      },
      {
        id: "status",
        area: STATUSBAR_AREAS.right,
        order: 140,
        render: function () { return jsx(FlowStatus, { ctx: ctx }); }
      }
    ]);
  }
};
