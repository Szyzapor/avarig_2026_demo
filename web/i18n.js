// UI strings (English / Polish). Keys are referenced from index.html via
// data-i18n="key" and from app.js via t("key").
window.I18N = {
  en: {
    title: "Binaural audio listening test",
    intro_lead:
      "Thank you for taking part. You will hear short recordings rendered for headphones by " +
      "different spatial-audio systems and rate how close each one sounds to a reference recording.",
    intro_time: "It takes about 15 minutes.",
    intro_req_h: "Before you start",
    intro_req_1: "Use headphones. The test does not work over loudspeakers.",
    intro_req_2: "Find a quiet place where you will not be interrupted.",
    intro_req_3: "Use a computer with a current browser (Chrome, Firefox, Safari or Edge). Phones work, but a computer is better.",
    intro_data_h: "Your data",
    intro_data_1:
      "The test is anonymous. We record your answers to a short questionnaire (age range, " +
      "playback device, experience with music and audio), your ratings and comments, and your browser type. " +
      "We do not collect your name, e-mail or IP address.",
    intro_data_2:
      "The answers are used only for research on spatial audio rendering and may be published in aggregated form. " +
      "You can stop at any time by closing the page.",
    intro_contact: "Questions:",
    consent: "I am 18 or older and I agree to take part in this listening test.",
    start: "Start",

    survey_h: "About you",
    survey_lead: "These answers help us interpret the ratings. Fields marked * are required.",
    q_age: "Age *",
    q_gender: "Gender",
    q_device: "What are you listening on? *",
    q_model: "Headphone model (optional)",
    q_model_ph: "e.g. Sennheiser HD 650, AirPods Pro",
    q_anc: "Active noise cancellation",
    q_env: "Listening environment *",
    q_hearing: "Do you have any known hearing impairment? *",
    q_music: "Experience with music *",
    q_audio: "Experience with audio / sound engineering *",
    q_spatial: "Familiarity with spatial or binaural audio (VR, games, 3D audio) *",
    q_tests: "Have you taken part in listening tests before? *",
    prefer_not: "Prefer not to say",
    continue: "Continue",
    fill_required: "Please answer all required questions.",

    age_u24: "18-24", age_25: "25-34", age_35: "35-44", age_45: "45-54", age_55: "55-64", age_65: "65 or older",
    g_f: "Female", g_m: "Male", g_o: "Other",
    dev_over_closed: "Over-ear headphones, closed-back",
    dev_over_open: "Over-ear headphones, open-back",
    dev_on_ear: "On-ear headphones",
    dev_iem: "In-ear earphones (wired)",
    dev_bt_buds: "Wireless earbuds (Bluetooth), e.g. AirPods",
    dev_bt_head: "Wireless headphones (Bluetooth)",
    dev_speakers: "Loudspeakers or laptop / phone speakers",
    dev_unknown: "Not sure",
    anc_on: "On", anc_off: "Off", anc_na: "My headphones don't have it / not sure",
    env_quiet: "Quiet room", env_some: "Some background noise", env_noisy: "Noisy (street, café, public transport)",
    yes: "Yes", no: "No", not_sure: "Not sure",
    mus_none: "None",
    mus_hobby: "Hobby (I play an instrument or sing, no formal training)",
    mus_edu: "Formal music education (music school, conservatory)",
    mus_pro: "Professional musician",
    aud_none: "None",
    aud_hobby: "Hobby (home recording, audiophile, mixing for fun)",
    aud_student: "Student of sound / audio engineering or acoustics",
    aud_pro: "Audio professional or researcher",
    sp_none: "I have not knowingly heard it before",
    sp_some: "Occasionally (VR, games, Spatial Audio on streaming services)",
    sp_reg: "Regularly / I work with it",
    tests_0: "Never", tests_1: "1-3 times", tests_4: "More than 3 times",

    check_h: "Headphone check",
    check_lead:
      "Put your headphones on. First set a comfortable volume, then confirm that the left and right sides are not swapped.",
    vol_h: "1. Volume",
    vol_text:
      "Play the sample and adjust your system volume so it is comfortable. Keep this volume for the rest of the test.",
    vol_play: "Play sample",
    vol_stop: "Stop",
    lr_h: "2. Left / right",
    lr_text: "Press play, then say which side the tone came from.",
    lr_play: "Play tone",
    lr_left: "Left",
    lr_right: "Right",
    lr_progress: "Tone {i} of {n}",
    lr_ok: "Left and right are correct.",
    lr_bad:
      "Some answers did not match. Check that your headphones are on the right way round (L on the left ear), then try again.",
    lr_retry: "Try again",
    check_continue: "Continue to instructions",

    instr_h: "How to rate",
    instr_1:
      "In each trial you hear one Reference recording and three versions of the same scene, labelled A, B and C. " +
      "The versions are shuffled in every trial.",
    instr_2:
      "All versions share one timeline: switch between them while playing (buttons or keys 1-4) to compare the same moment. " +
      "The clip loops. Space plays and pauses.",
    instr_3:
      "Rate how close each version sounds to the Reference. Consider both timbre (tone colour, artifacts) " +
      "and space (where sounds come from, width, whether they seem to come from outside your head).",
    instr_4: "Please listen to every version before rating it.",
    instr_scale: "Scale",
    instr_start: "Start the test",

    trial_h: "Trial {i} of {n}",
    rate_h: "Rate each version against the Reference",
    play_first: "Listen to this version first",
    comment_ph: "Optional comment (timbre, space, artifacts)",
    next: "Next trial",
    finish_trials: "Finish",
    rate_all: "Rate all three versions to continue.",
    loading: "Loading audio...",
    load_err: "Could not load the audio. Check your connection and reload the page.",
    ref_label: "Reference",
    sys_label: "Version {l}",
    shared_hint: "One version plays at a time on a shared timeline. Switch with the buttons or keys 1-4; Space = play/pause.",

    end_h: "Almost done",
    end_lead: "Anything else you would like to tell us about the test or the sounds? (optional)",
    end_comment_ph: "Your comments",
    submit: "Submit",
    thanks_h: "Thank you!",
    thanks_text: "Your answers have been saved.",
    thanks_offline:
      "The answers could not be sent automatically. Please download the file below and send it to the authors.",
    download: "Download my answers (JSON)",
    paper_text: "The systems compared in this test are described in our AES 2026 paper:",
    paper_link: "Read the paper",
    sending: "Sending...",

    mos_5: "Excellent", mos_5d: "imperceptible difference",
    mos_4: "Good", mos_4d: "perceptible, not annoying",
    mos_3: "Fair", mos_3d: "slightly annoying",
    mos_2: "Poor", mos_2d: "annoying",
    mos_1: "Bad", mos_1d: "very annoying",
  },

  pl: {
    title: "Test odsłuchowy dźwięku binauralnego",
    intro_lead:
      "Dziękujemy za udział. Usłyszysz krótkie nagrania przygotowane do odsłuchu na słuchawkach przez " +
      "różne systemy dźwięku przestrzennego i ocenisz, na ile każde z nich brzmi podobnie do nagrania referencyjnego.",
    intro_time: "Test trwa około 15 minut.",
    intro_req_h: "Zanim zaczniesz",
    intro_req_1: "Użyj słuchawek. Test nie działa na głośnikach.",
    intro_req_2: "Znajdź ciche miejsce, w którym nikt Ci nie przeszkodzi.",
    intro_req_3: "Użyj komputera z aktualną przeglądarką (Chrome, Firefox, Safari lub Edge). Telefon też zadziała, ale komputer jest lepszy.",
    intro_data_h: "Twoje dane",
    intro_data_1:
      "Test jest anonimowy. Zapisujemy odpowiedzi z krótkiej ankiety (przedział wieku, sprzęt odsłuchowy, " +
      "doświadczenie z muzyką i dźwiękiem), Twoje oceny i komentarze oraz typ przeglądarki. " +
      "Nie zbieramy imienia, adresu e-mail ani adresu IP.",
    intro_data_2:
      "Odpowiedzi posłużą wyłącznie do badań nad renderingiem dźwięku przestrzennego i mogą zostać opublikowane w formie zbiorczej. " +
      "Możesz przerwać w dowolnym momencie, zamykając stronę.",
    intro_contact: "Pytania:",
    consent: "Mam ukończone 18 lat i zgadzam się na udział w teście odsłuchowym.",
    start: "Rozpocznij",

    survey_h: "O Tobie",
    survey_lead: "Te odpowiedzi pomogą nam zinterpretować oceny. Pola oznaczone * są wymagane.",
    q_age: "Wiek *",
    q_gender: "Płeć",
    q_device: "Na czym słuchasz? *",
    q_model: "Model słuchawek (opcjonalnie)",
    q_model_ph: "np. Sennheiser HD 650, AirPods Pro",
    q_anc: "Aktywna redukcja szumów (ANC)",
    q_env: "Otoczenie podczas odsłuchu *",
    q_hearing: "Czy masz stwierdzone problemy ze słuchem? *",
    q_music: "Doświadczenie muzyczne *",
    q_audio: "Doświadczenie z realizacją / inżynierią dźwięku *",
    q_spatial: "Znajomość dźwięku przestrzennego lub binauralnego (VR, gry, dźwięk 3D) *",
    q_tests: "Czy brałeś/aś już udział w testach odsłuchowych? *",
    prefer_not: "Wolę nie podawać",
    continue: "Dalej",
    fill_required: "Odpowiedz na wszystkie wymagane pytania.",

    age_u24: "18-24", age_25: "25-34", age_35: "35-44", age_45: "45-54", age_55: "55-64", age_65: "65 lub więcej",
    g_f: "Kobieta", g_m: "Mężczyzna", g_o: "Inna",
    dev_over_closed: "Słuchawki wokółuszne, zamknięte",
    dev_over_open: "Słuchawki wokółuszne, otwarte",
    dev_on_ear: "Słuchawki nauszne",
    dev_iem: "Słuchawki douszne przewodowe",
    dev_bt_buds: "Bezprzewodowe słuchawki douszne (Bluetooth), np. AirPods",
    dev_bt_head: "Bezprzewodowe słuchawki nauszne / wokółuszne (Bluetooth)",
    dev_speakers: "Głośniki albo głośniki laptopa / telefonu",
    dev_unknown: "Nie wiem",
    anc_on: "Włączona", anc_off: "Wyłączona", anc_na: "Moje słuchawki jej nie mają / nie wiem",
    env_quiet: "Ciche pomieszczenie", env_some: "Trochę hałasu w tle", env_noisy: "Głośno (ulica, kawiarnia, komunikacja)",
    yes: "Tak", no: "Nie", not_sure: "Nie wiem",
    mus_none: "Brak",
    mus_hobby: "Hobbystycznie (gram na instrumencie lub śpiewam, bez formalnej edukacji)",
    mus_edu: "Formalna edukacja muzyczna (szkoła muzyczna, akademia)",
    mus_pro: "Zawodowy muzyk",
    aud_none: "Brak",
    aud_hobby: "Hobbystycznie (nagrania domowe, audiofil, miksowanie dla przyjemności)",
    aud_student: "Student realizacji dźwięku, inżynierii dźwięku lub akustyki",
    aud_pro: "Zawodowo zajmuję się dźwiękiem lub badaniami nad dźwiękiem",
    sp_none: "Świadomie się z nim nie spotkałem/am",
    sp_some: "Okazjonalnie (VR, gry, Spatial Audio w serwisach streamingowych)",
    sp_reg: "Regularnie / pracuję z nim",
    tests_0: "Nigdy", tests_1: "1-3 razy", tests_4: "Więcej niż 3 razy",

    check_h: "Sprawdzenie słuchawek",
    check_lead:
      "Załóż słuchawki. Najpierw ustaw wygodną głośność, potem sprawdź, czy lewa i prawa strona nie są zamienione.",
    vol_h: "1. Głośność",
    vol_text:
      "Odtwórz próbkę i ustaw głośność w systemie tak, żeby była wygodna. Nie zmieniaj jej do końca testu.",
    vol_play: "Odtwórz próbkę",
    vol_stop: "Zatrzymaj",
    lr_h: "2. Lewa / prawa",
    lr_text: "Naciśnij odtwarzanie i wskaż, z której strony był ton.",
    lr_play: "Odtwórz ton",
    lr_left: "Lewa",
    lr_right: "Prawa",
    lr_progress: "Ton {i} z {n}",
    lr_ok: "Lewa i prawa strona są poprawne.",
    lr_bad:
      "Część odpowiedzi się nie zgadza. Sprawdź, czy słuchawki są założone prawidłowo (L na lewym uchu), i spróbuj ponownie.",
    lr_retry: "Spróbuj ponownie",
    check_continue: "Przejdź do instrukcji",

    instr_h: "Jak oceniać",
    instr_1:
      "W każdej próbie usłyszysz nagranie referencyjne i trzy wersje tej samej sceny, oznaczone A, B i C. " +
      "Kolejność wersji zmienia się w każdej próbie.",
    instr_2:
      "Wszystkie wersje mają wspólną oś czasu: przełączaj je w trakcie odtwarzania (przyciski lub klawisze 1-4), żeby porównać ten sam moment. " +
      "Fragment odtwarza się w pętli. Spacja uruchamia i zatrzymuje odtwarzanie.",
    instr_3:
      "Oceń, na ile każda wersja brzmi podobnie do referencji. Weź pod uwagę barwę (brzmienie, zniekształcenia) " +
      "i przestrzeń (skąd dochodzą dźwięki, szerokość, czy dźwięk wydaje się dochodzić spoza głowy).",
    instr_4: "Przed oceną odsłuchaj każdą wersję.",
    instr_scale: "Skala",
    instr_start: "Rozpocznij test",

    trial_h: "Próba {i} z {n}",
    rate_h: "Oceń każdą wersję względem referencji",
    play_first: "Najpierw odsłuchaj tę wersję",
    comment_ph: "Komentarz opcjonalny (barwa, przestrzeń, zniekształcenia)",
    next: "Następna próba",
    finish_trials: "Zakończ",
    rate_all: "Oceń wszystkie trzy wersje, żeby przejść dalej.",
    loading: "Wczytywanie audio...",
    load_err: "Nie udało się wczytać audio. Sprawdź połączenie i odśwież stronę.",
    ref_label: "Referencja",
    sys_label: "Wersja {l}",
    shared_hint: "Naraz gra jedna wersja na wspólnej osi czasu. Przełączaj przyciskami lub klawiszami 1-4; Spacja = start/pauza.",

    end_h: "Prawie gotowe",
    end_lead: "Czy chcesz przekazać nam coś jeszcze o teście lub dźwiękach? (opcjonalnie)",
    end_comment_ph: "Twoje uwagi",
    submit: "Wyślij",
    thanks_h: "Dziękujemy!",
    thanks_text: "Twoje odpowiedzi zostały zapisane.",
    thanks_offline:
      "Nie udało się automatycznie wysłać odpowiedzi. Pobierz plik poniżej i wyślij go autorom.",
    download: "Pobierz moje odpowiedzi (JSON)",
    paper_text: "Systemy porównywane w tym teście opisujemy w naszym artykule na AES 2026:",
    paper_link: "Przeczytaj artykuł",
    sending: "Wysyłanie...",

    mos_5: "Doskonała", mos_5d: "różnica niezauważalna",
    mos_4: "Dobra", mos_4d: "słyszalna, nie przeszkadza",
    mos_3: "Średnia", mos_3d: "nieco przeszkadza",
    mos_2: "Słaba", mos_2d: "przeszkadza",
    mos_1: "Zła", mos_1d: "bardzo przeszkadza",
  },
};
