(() => {
  "use strict";

  const dialog = document.getElementById("devtools-dialog");
  const openButton = document.getElementById("devtools-open");
  if (!dialog || !openButton) {
    return;
  }

  const sourceButton = document.getElementById("load-source");
  const sourceView = document.getElementById("devtools-source");
  const requestButton = document.getElementById("load-request");
  const requestView = document.getElementById("devtools-request-info");
  const copyButton = document.getElementById("copy-url");

  openButton.addEventListener("click", () => {
    if (typeof dialog.showModal === "function") {
      if (!dialog.open) {
        dialog.showModal();
      }
    } else {
      dialog.setAttribute("open", "");
    }
  });

  dialog.addEventListener("click", (event) => {
    if (event.target === dialog && typeof dialog.close === "function") {
      dialog.close();
    }
  });

  if (sourceButton && sourceView) {
    sourceButton.addEventListener("click", async () => {
      sourceButton.disabled = true;
      sourceButton.textContent = "불러오는 중...";
      try {
        const response = await fetch(window.location.href, {
          credentials: "same-origin",
          cache: "no-store",
        });
        if (!response.ok) {
          throw new Error("HTTP " + response.status);
        }
        sourceView.textContent = await response.text();
        sourceView.hidden = false;
        sourceButton.textContent = "소스 새로고침";
      } catch (error) {
        sourceView.textContent = "소스를 불러오지 못했습니다: " + error.message;
        sourceView.hidden = false;
        sourceButton.textContent = "다시 시도";
      } finally {
        sourceButton.disabled = false;
      }
    });
  }

  if (requestButton && requestView) {
    requestButton.addEventListener("click", async () => {
      requestButton.disabled = true;
      requestButton.textContent = "불러오는 중...";
      try {
        const response = await fetch("/devtools/request", {
          credentials: "same-origin",
          cache: "no-store",
        });
        if (!response.ok) {
          throw new Error("HTTP " + response.status);
        }
        const info = await response.json();
        const headers = Array.isArray(info.headers)
          ? info.headers
          : Object.entries(info.headers || {});
        const lines = [
          "[현재 URL]",
          window.location.href,
          "",
          "[JavaScript에서 보이는 쿠키]",
          document.cookie || "(없음)",
          "",
          "[서버가 받은 요청 헤더]",
        ];
        for (const pair of headers) {
          if (Array.isArray(pair) && pair.length >= 2) {
            lines.push(`${pair[0]}: ${pair[1]}`);
          }
        }
        lines.push("");
        lines.push("[클라이언트] " + (info.client || "알 수 없음"));
        requestView.textContent = lines.join("\n");
        requestView.hidden = false;
        requestButton.textContent = "요청 정보 새로고침";
      } catch (error) {
        requestView.textContent = "요청 정보를 불러오지 못했습니다: " + error.message;
        requestView.hidden = false;
        requestButton.textContent = "다시 시도";
      } finally {
        requestButton.disabled = false;
      }
    });
  }

  if (copyButton) {
    copyButton.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(window.location.href);
        copyButton.textContent = "복사됨";
        window.setTimeout(() => {
          copyButton.textContent = "현재 URL 복사";
        }, 1500);
      } catch (error) {
        window.prompt("URL을 복사하세요:", window.location.href);
      }
    });
  }
})();
