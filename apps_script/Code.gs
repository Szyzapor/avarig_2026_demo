/**
 * Google Apps Script backend for the online MUSHRA test (web/).
 *
 * Setup (once):
 *   1. Create an empty Google Sheet; Extensions > Apps Script.
 *   2. Replace the editor contents with this file and save.
 *   3. Deploy > New deployment > type "Web app":
 *        Execute as: Me;  Who has access: Anyone.
 *   4. Copy the web-app URL (ends with /exec) into web/config.js -> endpoint.
 * After editing this script use Deploy > Manage deployments > Edit > New version.
 *
 * The page POSTs one JSON event per request (text/plain body):
 *   participant - questionnaire, headphone check, audio settings -> sheet "participants"
 *   page        - one MUSHRA page (7 conditions)                  -> sheet "mushra" (1 row per condition)
 *   finish      - comment, total time                             -> sheet "sessions"
 * Every event carries a unique event_id; repeats (client retries) are dropped.
 * Open the /exec URL in a browser to check that the deployment answers.
 */

var SURVEY_KEYS = ['age', 'hearing_impairment', 'device', 'headphone_model', 'environment',
                   'music_experience', 'audio_experience', 'spatial_audio_experience', 'listening_tests'];

var HEADERS = {
  participants: ['received_at', 'pid', 'session', 'session_uuid', 'client_time', 'started_at', 'lang', 'excluded']
    .concat(SURVEY_KEYS)
    .concat(['lr_correct', 'lr_total', 'lr_passed', 'lr_attempts', 'audio_sample_rate', 'audio_base_latency',
             'stimulus_sample_rate', 'attribute_order', 'n_pages', 'package', 'user_agent', 'screen', 'timezone',
             'event_id']),
  mushra: ['received_at', 'pid', 'session', 'session_uuid', 'client_time', 'page_index', 'n_pages', 'kind', 'block',
           'page_id', 'trial_id', 'dataset', 'clip', 'criterion', 'condition', 'label', 'score', 'listen_s',
           'reference_listen_s', 'page_seconds', 'event_id'],
  sessions: ['received_at', 'pid', 'session', 'session_uuid', 'client_time', 'n_pages', 'total_seconds', 'comment',
             'event_id'],
  events: ['received_at', 'event_id', 'type', 'pid', 'session']
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

function s_(v, n) {
  v = (v === undefined || v === null) ? '' : String(v);
  if (/^[=+\-@]/.test(v)) v = "'" + v;        // no formula injection from free text
  return v.slice(0, n || 500);
}

function seen_(eventId) {
  if (CacheService.getScriptCache().get(eventId)) return true;
  var ids = sheet_('events').getRange('B:B').getValues();
  for (var i = ids.length - 1; i > 0 && i > ids.length - 20000; i--) {
    if (ids[i][0] === eventId) return true;
  }
  return false;
}

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var ev = JSON.parse(e.postData.contents);
    if (!ev.event_id || !ev.pid || !ev.type) return out_('bad request');
    if (seen_(ev.event_id)) return out_('duplicate');
    var now = new Date();
    var head = [now, s_(ev.pid, 40), ev.session, s_(ev.session_uuid, 64), s_(ev.client_time, 40)];

    if (ev.type === 'participant') {
      var sv = ev.survey || {}, c = ev.check || {};
      sheet_('participants').appendRow(head
        .concat([s_(ev.started_at, 40), s_(ev.lang, 5), s_(ev.excluded || '', 40)])
        .concat(SURVEY_KEYS.map(function (k) { return s_(sv[k], 120); }))
        .concat([c.lr_correct, c.lr_total, c.lr_passed, c.lr_attempts, ev.audio_sample_rate, ev.audio_base_latency,
                 ev.stimulus_sample_rate, s_((ev.attribute_order || []).join(' '), 100), ev.n_pages,
                 s_(ev.package, 80), s_(ev.user_agent, 300), s_(ev.screen, 20), s_(ev.timezone, 60), ev.event_id]));
    } else if (ev.type === 'page') {
      var rows = (ev.ratings || []).map(function (r) {
        return head.concat([ev.page_index, ev.n_pages, s_(ev.kind, 10), ev.block, s_(ev.page_id, 100),
                            s_(ev.trial_id, 60), s_(ev.dataset, 30), s_(ev.clip, 40), s_(ev.criterion, 30),
                            s_(r.condition, 40), s_(r.label, 4), Number(r.score), r.listen_s,
                            ev.reference_listen_s, ev.page_seconds, ev.event_id]);
      });
      if (rows.length) {
        var sh = sheet_('mushra');
        sh.getRange(sh.getLastRow() + 1, 1, rows.length, rows[0].length).setValues(rows);
      }
    } else if (ev.type === 'finish') {
      sheet_('sessions').appendRow(head.concat([ev.n_pages, ev.total_seconds, s_(ev.comment, 3000), ev.event_id]));
    } else {
      return out_('unknown type');
    }
    sheet_('events').appendRow([now, ev.event_id, ev.type, s_(ev.pid, 40), ev.session]);
    CacheService.getScriptCache().put(ev.event_id, '1', 21600);
    return out_('ok');
  } catch (err) {
    return out_('error: ' + err);
  } finally {
    lock.releaseLock();
  }
}

function doGet() { return out_('MUSHRA endpoint is running'); }

function out_(msg) { return ContentService.createTextOutput(msg).setMimeType(ContentService.MimeType.TEXT); }
