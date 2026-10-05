// Deployment settings for the online listening test. Edit and commit.
window.TEST_CONFIG = {
  // Google Apps Script web-app URL that appends responses to a Google Sheet
  // (see apps_script/Code.gs and the README). Leave empty to run without a
  // backend: participants then get a "download responses" button at the end.
  endpoint: "",

  // Clips drawn at random per participant from EACH dataset in manifest.json.
  // 5 x 2 datasets = 10 trials, roughly 15 minutes.
  clipsPerDataset: 5,

  // A system must be played for at least this many seconds before it can be
  // rated (0 disables the check).
  minListenSeconds: 3,

  // Shown on the intro page if set.
  contactEmail: "",

  // Revealed only on the final page so it does not bias the ratings.
  paperUrl: "https://aes.org/publications/elibrary-page/?id=23351",
};
