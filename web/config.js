// Deployment settings for the online MUSHRA test. Edit and commit.
window.TEST_CONFIG = {
  // Google Apps Script web-app URL that appends results to a Google Sheet
  // (apps_script/Code.gs). Without it nothing is collected centrally; the
  // participant can still download their results as JSON at the end.
  endpoint: "",

  // Shown on the information page. Required before launch (consent).
  contactEmail: "",

  // A condition must be played this long (seconds) before its slider unlocks.
  minListenSeconds: 2,

  // Session 1: trials rated for overall quality, plus repeated trials that are
  // shown in a separate block after all originals (reliability check).
  session1Repeats: ["zhu__zhu_002", "argentum_pg__argentum_pg_003"],

  // Session 2: attribute blocks (order counterbalanced per participant by a
  // Latin square) on these trials, plus one repeated page.
  session2Trials: ["zhu__zhu_001", "zhu__zhu_003", "zhu__zhu_005",
                   "argentum_pg__argentum_pg_003", "argentum_pg__argentum_pg_005",
                   "argentum_pg__argentum_pg_021"],

  // Revealed only on the final page so it does not bias the ratings.
  paperUrl: "https://aes.org/publications/elibrary-page/?id=23351",
};
