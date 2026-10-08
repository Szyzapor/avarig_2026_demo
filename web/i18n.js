// UI strings (English / Polish). index.html uses data-i18n="key"; app.js uses t("key").
// Attribute wording paraphrases SAQI (Lindau et al. 2014); scale and instructions
// follow ITU-R BS.1534-3.
window.I18N = {
  en: {
    title: "Binaural audio listening test",
    s1_name: "Session 1 of 2: overall quality",
    s2_name: "Session 2 of 2: sound attributes",

    intro_lead:
      "You will hear short recordings of the same scenes rendered for headphones in several ways, and rate " +
      "how close each version is to a reference recording.",
    intro_s1: "This session takes about 25-30 minutes: 2 practice pages, then 14 rating pages.",
    intro_s2: "This session takes about 35 minutes: 1 practice page, then 4 blocks of 6 pages, one sound attribute per block.",
    intro_req_h: "Requirements",
    intro_req_1: "Wired headphones (over-ear, on-ear or in-ear). Bluetooth headphones and loudspeakers cannot be used.",
    intro_req_2: "A quiet place where you will not be interrupted, and one sitting without breaks longer than a few minutes.",
    intro_req_3: "A computer with a current browser (Chrome, Firefox, Safari or Edge).",
    intro_data_h: "Information and consent",
    intro_data_1:
      "The study compares methods for rendering spatial audio for headphones. Taking part is voluntary and you can " +
      "stop at any time by closing the page; unfinished sessions are kept only as far as they were completed.",
    intro_data_2:
      "We record your ratings, the questionnaire answers (age range, hearing, headphones, listening environment, " +
      "experience with music and audio), listening times, your browser type and its audio settings, and a participant " +
      "code. We do not record your name, e-mail or IP address. Results are used for research and published only in aggregated form.",
    intro_contact: "Contact:",
    consent: "I am 18 or older, I have read the information above and I agree to take part.",
    pid_label: "Participant code",
    start: "Start",

    survey_h: "About you",
    survey_h2: "Your setup today",
    survey_lead: "Fields marked * are required.",
    q_age: "Age *",
    q_hearing: "Do you have a known hearing impairment? *",
    q_device: "What are you listening on? *",
    q_model: "Headphone model * (write \"unknown\" if you don't know)",
    q_model_ph: "e.g. Sennheiser HD 650",
    q_env: "Listening environment *",
    q_music: "Experience with music *",
    q_audio: "Experience with audio / sound engineering *",
    q_spatial: "Experience with spatial or binaural audio *",
    q_tests: "Have you taken part in listening tests before? *",
    continue: "Continue",
    fill_required: "Please answer all required questions.",
    age_18: "18-24", age_25: "25-34", age_35: "35-44", age_45: "45-54", age_55: "55 or older", prefer_not: "Prefer not to say",
    yes: "Yes", no: "No", not_sure: "Not sure",
    dev_over_open: "Over-ear headphones, open-back (wired)",
    dev_over_closed: "Over-ear headphones, closed-back (wired)",
    dev_on_ear: "On-ear headphones (wired)",
    dev_in_ear: "In-ear headphones / earphones (wired)",
    dev_bluetooth: "Bluetooth / wireless headphones",
    dev_speakers: "Loudspeakers or laptop / phone speakers",
    env_quiet: "Quiet room", env_some: "Some background noise", env_noisy: "Noisy",
    mus_none: "None", mus_hobby: "Hobby", mus_edu: "Formal music education", mus_pro: "Professional musician",
    aud_none: "None", aud_hobby: "Hobby", aud_student: "Student of sound / audio engineering",
    aud_pro: "Audio professional or researcher",
    sp_none: "None", sp_some: "Occasional (VR, games, Spatial Audio)", sp_reg: "Regular / I work with it",
    tests_0: "Never", tests_1: "1-3 times", tests_4: "More than 3 times",

    excluded_h: "Wired headphones needed",
    excluded_text:
      "This test needs wired headphones: Bluetooth adds codec artefacts and delays, and loudspeakers cannot " +
      "reproduce binaural audio. Please come back with wired headphones and open the same link again. Thank you!",
    excluded_back: "Change my answer",

    check_h: "Headphone check",
    check_lead: "Put your headphones on. Set a comfortable volume, then confirm left and right.",
    vol_h: "1. Volume",
    vol_text: "Play the sample and set your system volume to a comfortable level. Do not change it during the session.",
    vol_play: "Play sample", vol_stop: "Stop",
    lr_h: "2. Left / right",
    lr_text: "Press play, then say which side the tone came from.",
    lr_play: "Play tone", lr_left: "Left", lr_right: "Right",
    lr_progress: "Tone {i} of {n}",
    lr_ok: "Left and right are correct.",
    lr_bad: "Some answers did not match. Check that the headphones are the right way round (L on the left ear) and try again.",
    lr_retry: "Try again",
    check_continue: "Continue",

    instr_h: "How to rate",
    instr_1:
      "Each page has a <b>reference</b> and seven versions of the same 10-second scene, numbered 1-7 in a new random " +
      "order on every page. One of them is a hidden copy of the reference, and some are deliberately degraded.",
    instr_2:
      "All versions share one timeline: switch between them while playing (buttons or keys 0-7, where 0 is the " +
      "reference) to compare the same moment. The excerpt loops; Space plays and pauses; you can drag the position bar.",
    instr_3:
      "Rate every version from 0 to 100 against the reference. If a version sounds identical to the reference " +
      "(the hidden reference), give it 100. Use the whole scale: the worst version on a page does not have to be 0.",
    instr_4:
      "A slider unlocks after you have listened to that version. You can go on once every version has been heard " +
      "and every slider has been set.",
    instr_scale: "Scale",
    instr_s2:
      "In this session each block asks about <b>one attribute</b>, so you will hear each scene four times. The " +
      "attribute is in the page title and described above the sliders. Rate only that attribute:",
    instr_start: "Start practice",

    page_training: "Practice {i} of {n}",
    page_progress: "{i} / {n}",
    training_note:
      "<b>Practice page, not analysed.</b> Listen to the reference and all versions, find the hidden reference and " +
      "the degraded versions, and try the sliders.",
    block_break: "Block {i} of {n} finished. Take a short break if you like.",
    ref: "Ref.",
    play_first: "listen first",
    unset: "-",
    missing_listen: "Listen to: {list}",
    missing_rate: "Set the slider for: {list}",
    next: "Next",
    loading: "Loading audio...",
    load_err: "Could not load the audio. Check your connection and reload the page; your progress is kept.",
    hint: "One version plays at a time on a shared timeline. Keys: 0 = reference, 1-7 = versions, Space = play/pause.",

    crit_overall: "Overall quality",
    crit_overall_d:
      "How close is each version to the reference overall, considering everything: tone colour, directions and width, " +
      "externalisation, and artefacts?",
    crit_tone_colour: "Tone colour",
    crit_tone_colour_d:
      "Balance of high and low frequencies (brighter or darker, more or less bass) compared with the reference. " +
      "Judge only tone colour.",
    crit_localisation: "Localisation and width",
    crit_localisation_d: "Are the sound sources in the same directions and as wide as in the reference?",
    crit_externalisation: "Externalisation",
    crit_externalisation_d: "Is the sound heard outside the head as in the reference, or more inside the head?",
    crit_artefacts: "Artefacts",
    crit_artefacts_d:
      "Added unwanted sounds that are not in the reference: distortion, noise, clicks, metallic or \"phasey\" sound. " +
      "100 = no added artefacts.",

    mos_5: "Excellent", mos_4: "Good", mos_3: "Fair", mos_2: "Poor", mos_1: "Bad",

    end_h: "Almost done",
    end_lead: "Anything you would like to tell us about the test or the sounds? (optional)",
    end_comment_ph: "Your comments",
    submit: "Finish and send",
    sending: "Sending...",
    thanks_h: "Thank you!",
    thanks_ok: "Your results have been sent.",
    thanks_offline:
      "Your results could not be sent automatically. Please download the file below and e-mail it to the contact address.",
    thanks_s2:
      "Session 2 (about 35 minutes) rates four sound attributes. Use this link, ideally on another day, with the same headphones:",
    thanks_pid: "Your participant code:",
    download: "Download my results (JSON)",
    paper_text: "The systems compared here are described in our AES 2026 paper:",
    paper_link: "Read the paper",
  },

  pl: {
    title: "Test odsłuchowy dźwięku binauralnego",
    s1_name: "Sesja 1 z 2: jakość ogólna",
    s2_name: "Sesja 2 z 2: cechy dźwięku",

    intro_lead:
      "Usłyszysz krótkie nagrania tych samych scen przygotowane do odsłuchu na słuchawkach na kilka sposobów i ocenisz, " +
      "na ile każda wersja jest podobna do nagrania referencyjnego.",
    intro_s1: "Ta sesja trwa około 25-30 minut: 2 strony próbne, potem 14 stron z ocenami.",
    intro_s2: "Ta sesja trwa około 35 minut: 1 strona próbna, potem 4 bloki po 6 stron, w każdym bloku jedna cecha dźwięku.",
    intro_req_h: "Wymagania",
    intro_req_1: "Słuchawki przewodowe (wokółuszne, nauszne lub douszne). Słuchawek Bluetooth ani głośników nie można używać.",
    intro_req_2: "Ciche miejsce, w którym nikt nie przeszkodzi, i jedno posiedzenie bez przerw dłuższych niż kilka minut.",
    intro_req_3: "Komputer z aktualną przeglądarką (Chrome, Firefox, Safari lub Edge).",
    intro_data_h: "Informacje i zgoda",
    intro_data_1:
      "Badanie porównuje metody renderowania dźwięku przestrzennego na słuchawki. Udział jest dobrowolny, możesz przerwać " +
      "w dowolnym momencie, zamykając stronę; z niedokończonej sesji zostaje tylko jej ukończona część.",
    intro_data_2:
      "Zapisujemy oceny, odpowiedzi z ankiety (przedział wieku, słuch, słuchawki, otoczenie, doświadczenie z muzyką i " +
      "dźwiękiem), czasy odsłuchu, typ przeglądarki i jej ustawienia audio oraz kod uczestnika. Nie zapisujemy imienia, " +
      "adresu e-mail ani adresu IP. Wyniki służą badaniom i są publikowane wyłącznie zbiorczo.",
    intro_contact: "Kontakt:",
    consent: "Mam ukończone 18 lat, przeczytałem/am powyższe informacje i zgadzam się na udział.",
    pid_label: "Kod uczestnika",
    start: "Rozpocznij",

    survey_h: "O Tobie",
    survey_h2: "Twój dzisiejszy sprzęt",
    survey_lead: "Pola oznaczone * są wymagane.",
    q_age: "Wiek *",
    q_hearing: "Czy masz stwierdzone problemy ze słuchem? *",
    q_device: "Na czym słuchasz? *",
    q_model: "Model słuchawek * (wpisz „nie wiem”, jeśli nie znasz)",
    q_model_ph: "np. Sennheiser HD 650",
    q_env: "Otoczenie *",
    q_music: "Doświadczenie muzyczne *",
    q_audio: "Doświadczenie z realizacją / inżynierią dźwięku *",
    q_spatial: "Doświadczenie z dźwiękiem przestrzennym lub binauralnym *",
    q_tests: "Czy brałeś/aś już udział w testach odsłuchowych? *",
    continue: "Dalej",
    fill_required: "Odpowiedz na wszystkie wymagane pytania.",
    age_18: "18-24", age_25: "25-34", age_35: "35-44", age_45: "45-54", age_55: "55 lub więcej", prefer_not: "Wolę nie podawać",
    yes: "Tak", no: "Nie", not_sure: "Nie wiem",
    dev_over_open: "Słuchawki wokółuszne otwarte (przewodowe)",
    dev_over_closed: "Słuchawki wokółuszne zamknięte (przewodowe)",
    dev_on_ear: "Słuchawki nauszne (przewodowe)",
    dev_in_ear: "Słuchawki douszne (przewodowe)",
    dev_bluetooth: "Słuchawki Bluetooth / bezprzewodowe",
    dev_speakers: "Głośniki albo głośniki laptopa / telefonu",
    env_quiet: "Ciche pomieszczenie", env_some: "Trochę hałasu w tle", env_noisy: "Głośno",
    mus_none: "Brak", mus_hobby: "Hobbystycznie", mus_edu: "Formalna edukacja muzyczna", mus_pro: "Zawodowy muzyk",
    aud_none: "Brak", aud_hobby: "Hobbystycznie", aud_student: "Student realizacji / inżynierii dźwięku",
    aud_pro: "Zawodowo lub naukowo",
    sp_none: "Brak", sp_some: "Okazjonalnie (VR, gry, Spatial Audio)", sp_reg: "Regularnie / pracuję z nim",
    tests_0: "Nigdy", tests_1: "1-3 razy", tests_4: "Więcej niż 3 razy",

    excluded_h: "Potrzebne słuchawki przewodowe",
    excluded_text:
      "Ten test wymaga słuchawek przewodowych: Bluetooth dodaje artefakty kodeka i opóźnienia, a głośniki nie odtworzą " +
      "dźwięku binauralnego. Wróć ze słuchawkami przewodowymi i otwórz ten sam link jeszcze raz. Dziękujemy!",
    excluded_back: "Zmień odpowiedź",

    check_h: "Sprawdzenie słuchawek",
    check_lead: "Załóż słuchawki. Ustaw wygodną głośność, potem sprawdź lewą i prawą stronę.",
    vol_h: "1. Głośność",
    vol_text: "Odtwórz próbkę i ustaw w systemie wygodną głośność. Nie zmieniaj jej do końca sesji.",
    vol_play: "Odtwórz próbkę", vol_stop: "Zatrzymaj",
    lr_h: "2. Lewa / prawa",
    lr_text: "Naciśnij odtwarzanie i wskaż, z której strony był ton.",
    lr_play: "Odtwórz ton", lr_left: "Lewa", lr_right: "Prawa",
    lr_progress: "Ton {i} z {n}",
    lr_ok: "Lewa i prawa strona są poprawne.",
    lr_bad: "Część odpowiedzi się nie zgadza. Sprawdź, czy słuchawki są dobrze założone (L na lewym uchu), i spróbuj ponownie.",
    lr_retry: "Spróbuj ponownie",
    check_continue: "Dalej",

    instr_h: "Jak oceniać",
    instr_1:
      "Na każdej stronie jest <b>referencja</b> i siedem wersji tej samej 10-sekundowej sceny, ponumerowanych 1-7 w nowej " +
      "losowej kolejności na każdej stronie. Jedna z nich to ukryta kopia referencji, a niektóre są celowo zdegradowane.",
    instr_2:
      "Wszystkie wersje mają wspólną oś czasu: przełączaj je w trakcie odtwarzania (przyciski lub klawisze 0-7, 0 to " +
      "referencja), żeby porównać ten sam moment. Fragment gra w pętli; Spacja uruchamia i zatrzymuje; pasek pozycji można przesuwać.",
    instr_3:
      "Oceń każdą wersję w skali 0-100 względem referencji. Jeśli wersja brzmi identycznie jak referencja (ukryta " +
      "referencja), daj 100. Korzystaj z całej skali: najgorsza wersja na stronie nie musi dostać 0.",
    instr_4:
      "Suwak odblokowuje się po odsłuchaniu danej wersji. Przejdziesz dalej, gdy odsłuchasz wszystkie wersje i ustawisz wszystkie suwaki.",
    instr_scale: "Skala",
    instr_s2:
      "W tej sesji każdy blok dotyczy <b>jednej cechy</b>, więc każdą scenę usłyszysz cztery razy. Cecha jest w tytule " +
      "strony i opisana nad suwakami. Oceniaj tylko tę cechę:",
    instr_start: "Rozpocznij próbę",

    page_training: "Próba {i} z {n}",
    page_progress: "{i} / {n}",
    training_note:
      "<b>Strona próbna, nie jest analizowana.</b> Posłuchaj referencji i wszystkich wersji, znajdź ukrytą referencję i " +
      "wersje zdegradowane, wypróbuj suwaki.",
    block_break: "Blok {i} z {n} zakończony. Jeśli chcesz, zrób krótką przerwę.",
    ref: "Ref.",
    play_first: "najpierw posłuchaj",
    unset: "-",
    missing_listen: "Posłuchaj: {list}",
    missing_rate: "Ustaw suwak dla: {list}",
    next: "Dalej",
    loading: "Wczytywanie audio...",
    load_err: "Nie udało się wczytać audio. Sprawdź połączenie i odśwież stronę; postęp jest zachowany.",
    hint: "Naraz gra jedna wersja na wspólnej osi czasu. Klawisze: 0 = referencja, 1-7 = wersje, Spacja = start/pauza.",

    crit_overall: "Jakość ogólna",
    crit_overall_d:
      "Na ile każda wersja jest podobna do referencji, biorąc pod uwagę wszystko: barwę, kierunki i szerokość, " +
      "eksternalizację i artefakty?",
    crit_tone_colour: "Barwa",
    crit_tone_colour_d:
      "Proporcja wysokich i niskich częstotliwości (jaśniej lub ciemniej, więcej lub mniej basu) w porównaniu z referencją. " +
      "Oceniaj tylko barwę.",
    crit_localisation: "Lokalizacja i szerokość",
    crit_localisation_d: "Czy źródła dźwięku są w tych samych kierunkach i tak samo szerokie jak w referencji?",
    crit_externalisation: "Eksternalizacja",
    crit_externalisation_d: "Czy dźwięk jest słyszany na zewnątrz głowy jak w referencji, czy bardziej w głowie?",
    crit_artefacts: "Artefakty",
    crit_artefacts_d:
      "Dodane niepożądane dźwięki, których nie ma w referencji: zniekształcenia, szum, trzaski, brzmienie metaliczne lub " +
      "„fazowe”. 100 = brak dodanych artefaktów.",

    mos_5: "Doskonała", mos_4: "Dobra", mos_3: "Dostateczna", mos_2: "Słaba", mos_1: "Zła",

    end_h: "Prawie gotowe",
    end_lead: "Czy chcesz przekazać nam coś o teście lub dźwiękach? (opcjonalnie)",
    end_comment_ph: "Twoje uwagi",
    submit: "Zakończ i wyślij",
    sending: "Wysyłanie...",
    thanks_h: "Dziękujemy!",
    thanks_ok: "Wyniki zostały wysłane.",
    thanks_offline:
      "Nie udało się automatycznie wysłać wyników. Pobierz plik poniżej i wyślij go na adres kontaktowy.",
    thanks_s2:
      "Sesja 2 (około 35 minut) dotyczy czterech cech dźwięku. Skorzystaj z tego linku, najlepiej innego dnia, na tych samych słuchawkach:",
    thanks_pid: "Twój kod uczestnika:",
    download: "Pobierz moje wyniki (JSON)",
    paper_text: "Porównywane systemy opisujemy w naszym artykule na AES 2026:",
    paper_link: "Przeczytaj artykuł",
  },
};
