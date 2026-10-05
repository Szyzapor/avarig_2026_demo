/**
 * Google Apps Script backend for the online listening test (web/).
 *
 * Setup (once):
 *   1. Create an empty Google Sheet; Extensions > Apps Script.
 *   2. Replace the editor contents with this file and save.
 *   3. Deploy > New deployment > type "Web app":
 *        Execute as: Me;  Who has access: Anyone.
 *   4. Copy the web-app URL (ends with /exec) into web/config.js -> endpoint.
 * After editing this script, use Deploy > Manage deployments > Edit > New
 * version, otherwise the old code keeps serving.
 *
 * The page POSTs one JSON event per request (text/plain body):
 *   participant - questionnaire + headphone check  -> sheet "participants"
 *   trial       - three MOS ratings for one clip    -> sheet "ratings" (1 row per system)
 *   finish      - final comment, total time         -> sheet "sessions"
 * Every event carries a unique event_id; repeats (client retries) are dropped.
 */

var SURVEY_KEYS = [
  'age', 'gender', 'device', 'headphone_model', 'anc', 'environment',
  'hearing_impairment', 'music_experience', 'audio_experience',
  'spatial_audio_experience', 'listening_tests'
];

var HEADERS = {
  participants: ['received_at', 'session_id', 'client_time', 'lang', 'started_at']
    .concat(SURVEY_KEYS)
    .concat(['lr_correct', 'lr_total', 'lr_passed', 'lr_attempts',
             'n_trials', 'user_agent', 'screen', 'timezone', 'event_id']),
  ratings: ['received_at', 'session_id', 'client_time', 'trial_index', 'n_trials',
            'dataset', 'clip_id', 'system', 'blind_label', 'mos', 'comment',
            'listen_s', 'reference_listen_s', 'trial_seconds', 'event_id'],
  sessions: ['received_at', 'session_id', 'client_time', 'n_completed',
             'total_seconds', 'final_comment', 'event_id'],
  events: ['received_at', 'event_id', 'type', 'session_id']
};

function sheet_(name) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    sh.appendRow(HEADERS[name]);
    sh.setFrozenRows(1);
  }
  return sh;
}

function clip_(v, n) {
  v = (v === undefined || v === null) ? '' : String(v);
  // Neutralise spreadsheet formula injection from free-text fields.
  if (/^[=+\-@]/.test(v)) v = "'" + v;
  return v.slice(0, n || 1000);
}

function seen_(eventId) {
  var cache = CacheService.getScriptCache();
  if (cache.get(eventId)) return true;
  var ids = sheet_('events').getRange('B:B').getValues();
  for (var i = ids.length - 1; i > 0 && i > ids.length - 5000; i--) {
    if (ids[i][0] === eventId) return true;
  }
  return false;
}

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var ev = JSON.parse(e.postData.contents);
    if (!ev.event_id || !ev.session_id || !ev.type) return out_('bad request');
    if (seen_(ev.event_id)) return out_('duplicate');
    var now = new Date();

    if (ev.type === 'participant') {
      var s = ev.survey || {}, c = ev.check || {};
      sheet_('participants').appendRow(
        [now, clip_(ev.session_id, 64), clip_(ev.client_time, 40), clip_(ev.lang, 5), clip_(ev.started_at, 40)]
          .concat(SURVEY_KEYS.map(function (k) { return clip_(s[k], 120); }))
          .concat([c.lr_correct, c.lr_total, c.lr_passed, c.lr_attempts, ev.n_trials,
                   clip_(ev.user_agent, 300), clip_(ev.screen, 20), clip_(ev.timezone, 60),
                   ev.event_id]));
    } else if (ev.type === 'trial') {
      var rows = (ev.ratings || []).map(function (r) {
        return [now, clip_(ev.session_id, 64), clip_(ev.client_time, 40), ev.trial_index, ev.n_trials,
                clip_(ev.dataset, 40), clip_(ev.clip_id, 40), clip_(r.system, 10), clip_(r.blind_label, 2),
                Number(r.mos), clip_(r.comment, 500), r.listen_s, ev.reference_listen_s,
                ev.trial_seconds, ev.event_id];
      });
      if (rows.length) {
        var sh = sheet_('ratings');
        sh.getRange(sh.getLastRow() + 1, 1, rows.length, rows[0].length).setValues(rows);
      }
    } else if (ev.type === 'finish') {
      sheet_('sessions').appendRow([now, clip_(ev.session_id, 64), clip_(ev.client_time, 40),
                                    ev.n_completed, ev.total_seconds, clip_(ev.final_comment, 3000),
                                    ev.event_id]);
    } else {
      return out_('unknown type');
    }

    sheet_('events').appendRow([now, ev.event_id, ev.type, clip_(ev.session_id, 64)]);
    CacheService.getScriptCache().put(ev.event_id, '1', 21600);
    return out_('ok');
  } catch (err) {
    return out_('error: ' + err);
  } finally {
    lock.releaseLock();
  }
}

function doGet() {
  return out_('listening-test endpoint is running');
}

function out_(msg) {
  return ContentService.createTextOutput(msg).setMimeType(ContentService.MimeType.TEXT);
}
