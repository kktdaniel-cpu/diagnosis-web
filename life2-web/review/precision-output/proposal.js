/* Review-only. Not loaded by the deployed diagnosis page until separately approved. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else factory().install(root);
})(typeof window !== 'undefined' ? window : this, function () {
  'use strict';
  const costScenarioExplanation = '현재 생활비를 변경해 같은 채점 엔진으로 다시 계산한 결과입니다. 65세 이후 목표 생활비는 그대로 유지합니다.';

  function canPrint(win, report) {
    try {
      return !!report && report.style.display !== 'none' &&
        win.localStorage.getItem('l2p_premium') === '1' && win._svDone === true &&
        typeof win.printReport === 'function';
    } catch (_) { return false; }
  }

  function sync(win) {
    const doc = win.document;
    const report = doc.getElementById('fullReportWrap');
    let actions = doc.getElementById('l2p-report-print-actions');
    if (!canPrint(win, report)) {
      if (actions) actions.hidden = true;
      return;
    }
    if (!actions) {
      actions = doc.createElement('div');
      actions.id = 'l2p-report-print-actions';
      actions.className = 'l2p-report-print-actions';
      actions.style.cssText = 'margin:12px 0;padding:12px;border:1px solid #D7DED8;border-radius:12px;background:#fff';
      const button = doc.createElement('button');
      button.type = 'button';
      button.className = 'btn-pdf-on';
      button.addEventListener('click', function () {
        if (canPrint(win, doc.getElementById('fullReportWrap'))) win.printReport();
      });
      actions.appendChild(button);
      // Keep the action inside the unlocked report, outside the survey/gate fragments.
      report.insertBefore(actions, report.firstChild);
    } else if (actions.parentNode !== report) {
      report.insertBefore(actions, report.firstChild);
    }
    const label = win.L2P_LANG === 'en' ? 'Save PDF / Print' : 'PDF 저장 / 인쇄';
    if (actions.firstChild.textContent !== label) actions.firstChild.textContent = label;
    actions.hidden = false;
  }

  function install(win) {
    if (win.__l2pPrintEntryInstalled) return;
    win.__l2pPrintEntryInstalled = true;
    const style = win.document.createElement('style');
    style.textContent = '@media print{.l2p-report-print-actions{display:none!important}}';
    win.document.head.appendChild(style);
    for (const name of ['renderReportFromServer', 'unlockPremium', 'submitSurvey', 'l2pOpenFullReport']) {
      const original = win[name];
      if (typeof original !== 'function') continue;
      win[name] = function () {
        const result = original.apply(this, arguments);
        sync(win);
        return result;
      };
    }
    // Handles asynchronous report replacement without touching Auth, FACTs or calculations.
    if (win.MutationObserver) {
      const observer = new win.MutationObserver(function () { sync(win); });
      observer.observe(win.document.body, { childList: true, subtree: true });
    }
    sync(win);
  }
  return { costScenarioExplanation, canPrint, sync, install };
});
