#!/usr/bin/env python3
"""Builds the pt-BR and es legal pages from the English ones (issue solevia-studio#208).

    python3 tools/build_legal.py

The English pages (privacy/<slug>/index.html, terms/<slug>/index.html) stay the source of
truth. This script
  1. adds hreflang links and a language switch to each English page (idempotent), and
  2. writes /pt/privacy/<slug>/, /pt/terms/<slug>/, /es/privacy/<slug>/, /es/terms/<slug>/
     by replacing each English block with its translation from TR below.
It refuses to run if an English block has no translation, so a copy change in English shows up
as a failed build instead of a silently stale translation. Adding a game = add its slug to GAMES.
Python 3, no dependencies. Text is translated by hand (no machine translation at build time).
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://solevia.app"

# slug -> English display name (as written in the English pages)
GAMES = {
    "pop-zen": "Zen Bubbles",
    "cap-kickers": "Cap Kickers",
    "squish-sort": "Squish Sort",
    "ring-haven": "Ring Haven: Calm Ring Puzzle",
}
KINDS = ("privacy", "terms")
LANGS = {  # code -> (html lang, hreflang, label)
    "en": ("en", "en", "English"),
    "pt": ("pt-BR", "pt-BR", "Português"),
    "es": ("es-419", "es-419", "Español"),
}

# --- translations -----------------------------------------------------------------------
# Key = start of the English block (after the game name is replaced with {G}); the longest
# matching key wins. Value = (pt-BR, es-419). {G} = game name, {PRIV} = this game's privacy
# page in the same language. HTML entities are kept as in the English pages.
IOS_P = ("iOS: Ajustes &rarr; Privacidade e Segurança &rarr; Rastreamento",
         "iOS: Configuración &rarr; Privacidad y seguridad &rarr; Rastreo")
TR = {
 "← Sole Via Entertainment": ("← Sole Via Entertainment", "← Sole Via Entertainment"),
 "Privacy Policy — {G}": ("Política de Privacidade — {G}", "Política de Privacidad — {G}"),
 "Terms of Use — {G}": ("Termos de Uso — {G}", "Términos de Uso — {G}"),
 "Last updated: September 1, 2026": ("Última atualização: 1 de setembro de 2026", "Última actualización: 1 de septiembre de 2026"),
 "Last updated: September 25, 2026": ("Última atualização: 25 de setembro de 2026", "Última actualización: 25 de septiembre de 2026"),
 "Last updated: October 5, 2026": ("Última atualização: 5 de outubro de 2026", "Última actualización: 5 de octubre de 2026"),

 # ---- privacy: shared
 "This page is maintained by the app owner": (
  "Esta página é mantida pelo proprietário do app (&ldquo;nós&rdquo;) para explicar como o {G} (&ldquo;o App&rdquo;) trata as informações. O App foi pensado para ser aproveitado sem criar conta e sem coletar informações pessoais em nossos próprios servidores.",
  "Esta página la mantiene el propietario de la app (&ldquo;nosotros&rdquo;) para explicar cómo {G} (&ldquo;la App&rdquo;) trata la información. La App está pensada para disfrutarse sin crear una cuenta y sin recopilar información personal en nuestros propios servidores."),
 "Information stored on your device": ("Informações armazenadas no seu dispositivo", "Información almacenada en tu dispositivo"),
 "The App saves your game settings, your chosen cap": (
  "O App salva suas configurações de jogo, a tampinha e o campo escolhidos e o progresso da campanha no armazenamento local do dispositivo, para você continuar de onde parou. Esses dados ficam no seu dispositivo e não são enviados para nós. Desinstalar o App os remove.",
  "La App guarda tus ajustes de juego, la chapa y la cancha que elegiste y el progreso de tu campaña en el almacenamiento local del dispositivo, para que continúes donde lo dejaste. Estos datos permanecen en tu dispositivo y no se nos envían. Al desinstalar la App se eliminan."),
 "The App saves your per-phase best scores": (
  "O App salva seus melhores resultados e tempos por fase no armazenamento local do dispositivo, para você acompanhar seu próprio progresso. Esses dados ficam no seu dispositivo. Você pode apagá-los quando quiser na tela de Recordes (Apagar recordes) ou desinstalando o App.",
  "La App guarda tus mejores puntajes y tiempos por fase en el almacenamiento local del dispositivo, para que sigas tu propio progreso. Estos datos permanecen en tu dispositivo. Puedes borrarlos cuando quieras desde la pantalla de Récords (Borrar récords) o desinstalando la App."),
 "The App saves your level progress, Glow balance": (
  "O App salva seu progresso de fases, seu saldo de Glow, as skins e os fundos que você tem, a sequência e os presentes do Anel do Dia, seus melhores resultados e suas configurações (idioma, som, música, vibração, lembrete diário) no armazenamento local do dispositivo, para você continuar de onde parou. Esses dados ficam no seu dispositivo e não são enviados para nós. Desinstalar o App os remove.",
  "La App guarda tu progreso de niveles, tu saldo de Glow, los estilos y fondos que tienes, la racha y los regalos del Anillo Diario, tus mejores resultados y tus ajustes (idioma, sonido, música, vibración, recordatorio diario) en el almacenamiento local del dispositivo, para que continúes donde lo dejaste. Estos datos permanecen en tu dispositivo y no se nos envían. Al desinstalar la App se eliminan."),
 "The App saves your Fluff balance": (
  "O App salva seu saldo de Fluff, as skins e os temas de pote que você tem, seu progresso de fases e a sequência do Desafio Diário no armazenamento local do dispositivo, para você continuar de onde parou. Esses dados ficam no seu dispositivo e não são enviados para nós. Desinstalar o App os remove.",
  "La App guarda tu saldo de Fluff, los estilos y temas de frasco que tienes, tu progreso de niveles y la racha del Desafío Diario en el almacenamiento local del dispositivo, para que continúes donde lo dejaste. Estos datos permanecen en tu dispositivo y no se nos envían. Al desinstalar la App se eliminan."),
 "Information we do not collect": ("Informações que não coletamos", "Información que no recopilamos"),
 "We do not require sign-in.": ("Não exigimos login.", "No exigimos iniciar sesión."),
 "We do not collect your name, email": ("Não coletamos seu nome, e-mail nem informações de contato.", "No recopilamos tu nombre, correo electrónico ni datos de contacto."),
 "We do not access your location (GPS)": ("Não acessamos sua localização (GPS), câmera, microfone, fotos nem contatos.", "No accedemos a tu ubicación (GPS), cámara, micrófono, fotos ni contactos."),
 "We do not sell personal information.": ("Não vendemos informações pessoais.", "No vendemos información personal."),
 "Usage analytics": ("Análise de uso", "Analíticas de uso"),
 "We use Google Analytics for Firebase to understand how the game is played &mdash; which levels get completed, where players": (
  "Usamos o Google Analytics para Firebase para entender como o jogo é jogado &mdash; quais fases são concluídas, onde os jogadores saem do tutorial e quais idiomas e configurações são usados. Esses relatórios são anônimos e agregados. Eles incluem um identificador da instância do app gerado pelo Firebase, o modelo do seu dispositivo, a versão do sistema operacional e um país aproximado, obtido a partir do seu endereço IP. Não coletamos seu nome, e-mail nem localização precisa, não definimos ID de usuário e não vinculamos esses dados à sua identidade. Também recebemos relatórios agregados de receita de anúncios por meio da ligação entre o Google AdMob e o Firebase. Você pode desativar a análise de uso a qualquer momento no App, em Ajustes &rarr; Análise de uso; o jogo funciona exatamente igual com ela desativada. Veja as <a href=\"https://firebase.google.com/support/privacy\">informações de privacidade e segurança do Firebase</a>, do Google.",
  "Usamos Google Analytics para Firebase para entender cómo se juega &mdash; qué niveles se completan, dónde abandonan los jugadores el tutorial y qué idiomas y ajustes se usan. Estos informes son anónimos y agregados. Incluyen un identificador de la instancia de la app generado por Firebase, el modelo de tu dispositivo, la versión del sistema operativo y un país aproximado, obtenido a partir de tu dirección IP. No recopilamos tu nombre, correo electrónico ni ubicación precisa, no establecemos un ID de usuario y no vinculamos estos datos con tu identidad. También recibimos informes agregados de ingresos por anuncios mediante el vínculo entre Google AdMob y Firebase. Puedes desactivar las analíticas de uso en cualquier momento dentro de la App, en Ajustes &rarr; Analíticas de uso; el juego funciona exactamente igual con ellas desactivadas. Consulta la <a href=\"https://firebase.google.com/support/privacy\">información de privacidad y seguridad de Firebase</a>, de Google."),
 "We use Google Analytics for Firebase to understand how the game is played &mdash; which modes and worlds": (
  "Usamos o Google Analytics para Firebase para entender como o jogo é jogado &mdash; quais modos e mundos as pessoas jogam, como as partidas começam e terminam, quais skins e desafios diários são usados e onde os jogadores desistem &mdash; para podermos melhorar o jogo. Esses relatórios são anônimos e agregados. Eles incluem um identificador da instância do app gerado pelo Firebase, o modelo do seu dispositivo, a versão do sistema operacional e um país aproximado, obtido a partir do seu endereço IP. Não coletamos seu nome, e-mail nem localização precisa, não definimos ID de usuário e não vinculamos esses dados à sua identidade. Também recebemos relatórios agregados de receita de anúncios por meio da ligação entre o Google AdMob e o Firebase. Você pode desativar a análise de uso a qualquer momento no App, em Ajustes &rarr; Análises; o jogo funciona exatamente igual com ela desativada. Veja as <a href=\"https://firebase.google.com/support/privacy\">informações de privacidade e segurança do Firebase</a>, do Google.",
  "Usamos Google Analytics para Firebase para entender cómo se juega &mdash; qué modos y mundos juega la gente, cómo empiezan y terminan las partidas, qué estilos y desafíos diarios se usan y dónde abandonan los jugadores &mdash; para poder mejorar el juego. Estos informes son anónimos y agregados. Incluyen un identificador de la instancia de la app generado por Firebase, el modelo de tu dispositivo, la versión del sistema operativo y un país aproximado, obtenido a partir de tu dirección IP. No recopilamos tu nombre, correo electrónico ni ubicación precisa, no establecemos un ID de usuario y no vinculamos estos datos con tu identidad. También recibimos informes agregados de ingresos por anuncios mediante el vínculo entre Google AdMob y Firebase. Puedes desactivar las analíticas de uso en cualquier momento dentro de la App, en Ajustes &rarr; Analíticas; el juego funciona exactamente igual con ellas desactivadas. Consulta la <a href=\"https://firebase.google.com/support/privacy\">información de privacidad y seguridad de Firebase</a>, de Google."),
 "We use Google Analytics for Firebase to understand how the game is played &mdash; which levels get completed, how the Daily": (
  "Usamos o Google Analytics para Firebase para entender como o jogo é jogado &mdash; quais fases são concluídas, como {DAILY_PT} e a sequência são usados e quais idiomas e configurações são usados. Esses relatórios são anônimos e agregados. Eles incluem um identificador da instância do app gerado pelo Firebase, o modelo do seu dispositivo, a versão do sistema operacional e um país aproximado, obtido a partir do seu endereço IP. Não coletamos seu nome, e-mail nem localização precisa, não definimos ID de usuário e não vinculamos esses dados à sua identidade. Também recebemos relatórios agregados de receita de anúncios por meio da ligação entre o Google AdMob e o Firebase. Veja as <a href=\"https://firebase.google.com/support/privacy\">informações de privacidade e segurança do Firebase</a>, do Google.",
  "Usamos Google Analytics para Firebase para entender cómo se juega &mdash; qué niveles se completan, cómo se usan {DAILY_ES} y la racha, y qué idiomas y ajustes se usan. Estos informes son anónimos y agregados. Incluyen un identificador de la instancia de la app generado por Firebase, el modelo de tu dispositivo, la versión del sistema operativo y un país aproximado, obtenido a partir de tu dirección IP. No recopilamos tu nombre, correo electrónico ni ubicación precisa, no establecemos un ID de usuario y no vinculamos estos datos con tu identidad. También recibimos informes agregados de ingresos por anuncios mediante el vínculo entre Google AdMob y Firebase. Consulta la <a href=\"https://firebase.google.com/support/privacy\">información de privacidad y seguridad de Firebase</a>, de Google."),
 "Advertising": ("Publicidade", "Publicidad"),
 "The App displays advertisements to support development.": (
  "O App exibe anúncios para apoiar o desenvolvimento. Quando a publicidade está ativada nas versões das lojas, por meio do Google AdMob, o SDK de anúncios pode coletar informações como o identificador de publicidade do seu dispositivo, localização aproximada derivada do IP, dados de interação com o app e de publicidade e informações técnicas do dispositivo, para veicular e medir anúncios. No iOS, será solicitada sua permissão de Transparência de Rastreamento de Apps antes de qualquer identificador de rastreamento ser usado; recusar não impede você de jogar, você apenas pode ver anúncios menos relevantes. Veja o aviso de privacidade de publicidade do Google em <a href=\"https://policies.google.com/technologies/ads\">policies.google.com/technologies/ads</a>.",
  "La App muestra anuncios para apoyar el desarrollo. Cuando la publicidad está activada en las versiones de las tiendas, mediante Google AdMob, el SDK de anuncios puede recopilar información como el identificador de publicidad de tu dispositivo, la ubicación aproximada derivada de la IP, datos de interacción con la app y de publicidad e información técnica del dispositivo, para mostrar y medir anuncios. En iOS se te pedirá permiso de Transparencia de Seguimiento de Apps antes de usar cualquier identificador de seguimiento; si lo rechazas puedes seguir jugando, solo que podrías ver anuncios menos relevantes. Consulta el aviso de privacidad de publicidad de Google en <a href=\"https://policies.google.com/technologies/ads\">policies.google.com/technologies/ads</a>."),
 "The App displays banner, interstitial and rewarded-video advertisements to support development, served through Google AdMob. Rewarded ads (&ldquo;next move&rdquo;": (
  "O App exibe anúncios em banner, intersticiais e em vídeo com recompensa para apoiar o desenvolvimento, veiculados pelo Google AdMob. Os anúncios com recompensa (&ldquo;próximo movimento&rdquo;, &ldquo;desfazer um elo&rdquo;, &ldquo;Glow em dobro&rdquo;) são sempre opcionais &mdash; todas as fases podem ser concluídas sem assistir a nenhum. Quando a publicidade está ativada nas versões das lojas, o SDK de anúncios pode coletar informações como o identificador de publicidade do seu dispositivo, localização aproximada derivada do IP, dados de interação com o app e de publicidade e informações técnicas do dispositivo, para veicular e medir anúncios. No iOS, será solicitada sua permissão de Transparência de Rastreamento de Apps antes de qualquer identificador de rastreamento ser usado; recusar não impede você de jogar, você apenas pode ver anúncios menos relevantes. Veja o aviso de privacidade de publicidade do Google em <a href=\"https://policies.google.com/technologies/ads\">policies.google.com/technologies/ads</a>.",
  "La App muestra anuncios de banner, intersticiales y de video con recompensa para apoyar el desarrollo, servidos mediante Google AdMob. Los anuncios con recompensa (&ldquo;siguiente movimiento&rdquo;, &ldquo;desvincular uno&rdquo;, &ldquo;Glow doble&rdquo;) son siempre opcionales &mdash; todos los niveles se pueden terminar sin ver ninguno. Cuando la publicidad está activada en las versiones de las tiendas, el SDK de anuncios puede recopilar información como el identificador de publicidad de tu dispositivo, la ubicación aproximada derivada de la IP, datos de interacción con la app y de publicidad e información técnica del dispositivo, para mostrar y medir anuncios. En iOS se te pedirá permiso de Transparencia de Seguimiento de Apps antes de usar cualquier identificador de seguimiento; si lo rechazas puedes seguir jugando, solo que podrías ver anuncios menos relevantes. Consulta el aviso de privacidad de publicidad de Google en <a href=\"https://policies.google.com/technologies/ads\">policies.google.com/technologies/ads</a>."),
 "The App displays banner, interstitial and rewarded-video advertisements to support development, served through Google AdMob. Rewarded ads (&ldquo;extra jar&rdquo;": (
  "O App exibe anúncios em banner, intersticiais e em vídeo com recompensa para apoiar o desenvolvimento, veiculados pelo Google AdMob. Os anúncios com recompensa (&ldquo;pote extra&rdquo;, &ldquo;desfazer&rdquo;) são sempre opcionais &mdash; todas as fases podem ser concluídas sem assistir a nenhum. Quando a publicidade está ativada nas versões das lojas, o SDK de anúncios pode coletar informações como o identificador de publicidade do seu dispositivo, localização aproximada derivada do IP, dados de interação com o app e de publicidade e informações técnicas do dispositivo, para veicular e medir anúncios. No iOS, será solicitada sua permissão de Transparência de Rastreamento de Apps antes de qualquer identificador de rastreamento ser usado; recusar não impede você de jogar, você apenas pode ver anúncios menos relevantes. Veja o aviso de privacidade de publicidade do Google em <a href=\"https://policies.google.com/technologies/ads\">policies.google.com/technologies/ads</a>.",
  "La App muestra anuncios de banner, intersticiales y de video con recompensa para apoyar el desarrollo, servidos mediante Google AdMob. Los anuncios con recompensa (&ldquo;frasco extra&rdquo;, &ldquo;deshacer&rdquo;) son siempre opcionales &mdash; todos los niveles se pueden terminar sin ver ninguno. Cuando la publicidad está activada en las versiones de las tiendas, el SDK de anuncios puede recopilar información como el identificador de publicidad de tu dispositivo, la ubicación aproximada derivada de la IP, datos de interacción con la app y de publicidad e información técnica del dispositivo, para mostrar y medir anuncios. En iOS se te pedirá permiso de Transparencia de Seguimiento de Apps antes de usar cualquier identificador de seguimiento; si lo rechazas puedes seguir jugando, solo que podrías ver anuncios menos relevantes. Consulta el aviso de privacidad de publicidad de Google en <a href=\"https://policies.google.com/technologies/ads\">policies.google.com/technologies/ads</a>."),
 "Daily reminder (local notifications)": ("Lembrete diário (notificações locais)", "Recordatorio diario (notificaciones locales)"),
 "If you turn on the Daily Ring reminder": (
  "Se você ativar o lembrete do Anel do Dia em Ajustes, o App pede ao seu dispositivo permissão para mostrar uma notificação local em um horário do dia. O lembrete é agendado somente no seu dispositivo; nenhum dado de notificação é enviado para nós. Ele vem desativado por padrão e você pode desativá-lo a qualquer momento em Ajustes ou nas configurações de notificações do seu dispositivo.",
  "Si activas el recordatorio del Anillo Diario en Ajustes, la App le pide permiso a tu dispositivo para mostrar una notificación local a una hora del día. El recordatorio se programa solo en tu dispositivo; no se nos envía ningún dato de notificaciones. Viene desactivado por defecto y puedes desactivarlo en cualquier momento en Ajustes o en los ajustes de notificaciones de tu dispositivo."),
 "Consent and privacy choices": ("Consentimento e escolhas de privacidade", "Consentimiento y opciones de privacidad"),
 "Where required (for example in the EEA": (
  "Quando exigido (por exemplo, no EEE, no Reino Unido, na Suíça e em alguns estados dos EUA), o App usa o mecanismo de consentimento do Google (a User Messaging Platform) para pedir suas escolhas antes de exibir anúncios personalizados. Você pode revisar ou alterar sua escolha a qualquer momento no botão &ldquo;Escolhas de privacidade&rdquo; nos Ajustes do App.",
  "Cuando se requiere (por ejemplo, en el EEE, el Reino Unido, Suiza y algunos estados de EE. UU.), la App usa el mecanismo de consentimiento de Google (la User Messaging Platform) para pedirte tus opciones antes de mostrar anuncios personalizados. Puedes revisar o cambiar tu elección en cualquier momento con el botón &ldquo;Opciones de privacidad&rdquo; en los Ajustes de la App."),
 "Consent in the EEA, UK and Switzerland": ("Consentimento no EEE, no Reino Unido e na Suíça", "Consentimiento en el EEE, el Reino Unido y Suiza"),
 "Where required, the App uses Google": (
  "Quando exigido, o App usa o mecanismo de consentimento do Google (o SDK UMP) para pedir seu consentimento antes de exibir anúncios personalizados.",
  "Cuando se requiere, la App usa el mecanismo de consentimiento de Google (el SDK UMP) para pedir tu consentimiento antes de mostrar anuncios personalizados."),
 "Your US state privacy rights": ("Seus direitos de privacidade nos estados dos EUA", "Tus derechos de privacidad en los estados de EE. UU."),
 "We do not sell your personal information for money. Using your advertising identifier for personalized ads may be considered &ldquo;sharing&rdquo;/a &ldquo;sale&rdquo; under some US state laws. You can opt out by declining the tracking prompt (iOS), using": (
  "Não vendemos suas informações pessoais por dinheiro. Usar seu identificador de publicidade para anúncios personalizados pode ser considerado &ldquo;compartilhamento&rdquo; ou &ldquo;venda&rdquo; segundo algumas leis estaduais dos EUA. Você pode optar por sair recusando o pedido de rastreamento (iOS), usando &ldquo;Escolhas de privacidade&rdquo; nos Ajustes ou limitando a personalização de anúncios nas configurações do seu dispositivo.",
  "No vendemos tu información personal a cambio de dinero. Usar tu identificador de publicidad para anuncios personalizados puede considerarse &ldquo;compartir&rdquo; o &ldquo;vender&rdquo; según algunas leyes estatales de EE. UU. Puedes darte de baja rechazando la solicitud de seguimiento (iOS), usando &ldquo;Opciones de privacidad&rdquo; en Ajustes o limitando la personalización de anuncios en los ajustes de tu dispositivo."),
 "We do not sell your personal information for money. Using your advertising identifier for personalized ads may be considered &ldquo;sharing&rdquo;/a &ldquo;sale&rdquo; under some US state laws. You can opt out by declining the tracking prompt (iOS), withholding": (
  "Não vendemos suas informações pessoais por dinheiro. Usar seu identificador de publicidade para anúncios personalizados pode ser considerado &ldquo;compartilhamento&rdquo; ou &ldquo;venda&rdquo; segundo algumas leis estaduais dos EUA. Você pode optar por sair recusando o pedido de rastreamento (iOS), negando o consentimento para publicidade ou limitando a personalização de anúncios nas configurações do seu dispositivo.",
  "No vendemos tu información personal a cambio de dinero. Usar tu identificador de publicidad para anuncios personalizados puede considerarse &ldquo;compartir&rdquo; o &ldquo;vender&rdquo; según algunas leyes estatales de EE. UU. Puedes darte de baja rechazando la solicitud de seguimiento (iOS), negando el consentimiento de publicidad o limitando la personalización de anuncios en los ajustes de tu dispositivo."),
 "Children": ("Crianças", "Niños"),
 "The App is a general-audience sports game": (
  "O App é um jogo de esportes para todos os públicos e não é direcionado a crianças menores de 13 anos. Não coletamos intencionalmente informações pessoais de crianças.",
  "La App es un juego deportivo para todo público y no está dirigido a niños menores de 13 años. No recopilamos a sabiendas información personal de niños."),
 "The App is a general-audience relaxation game": (
  "O App é um jogo de relaxamento para todos os públicos e não é direcionado a crianças menores de 13 anos. Não coletamos intencionalmente informações pessoais de crianças.",
  "La App es un juego de relajación para todo público y no está dirigido a niños menores de 13 años. No recopilamos a sabiendas información personal de niños."),
 "The App is a general-audience puzzle game": (
  "O App é um quebra-cabeça para todos os públicos e não é direcionado a crianças menores de 13 anos. Não coletamos intencionalmente informações pessoais de crianças.",
  "La App es un juego de puzzles para todo público y no está dirigido a niños menores de 13 años. No recopilamos a sabiendas información personal de niños."),
 "Your choices": ("Suas escolhas", "Tus opciones"),
 "You can turn usage analytics off in the App under Settings &rarr; Usage Analytics. You can change": (
  "Você pode desativar a análise de uso no App, em Ajustes &rarr; Análise de uso. Você pode alterar sua escolha de rastreamento de anúncios a qualquer momento (iOS: Ajustes &rarr; Privacidade e Segurança &rarr; Rastreamento). Você pode limitar a personalização de anúncios nas configurações do dispositivo (iOS: Ajustes &rarr; Privacidade e Segurança &rarr; Publicidade da Apple; Android: Configurações &rarr; Google &rarr; Anúncios). Excluir o App remove as configurações e o progresso armazenados no seu dispositivo.",
  "Puedes desactivar las analíticas de uso en la App, en Ajustes &rarr; Analíticas de uso. Puedes cambiar tu elección de seguimiento de anuncios en cualquier momento (iOS: Configuración &rarr; Privacidad y seguridad &rarr; Rastreo). Puedes limitar la personalización de anuncios desde los ajustes del dispositivo (iOS: Configuración &rarr; Privacidad y seguridad &rarr; Publicidad de Apple; Android: Configuración &rarr; Google &rarr; Anuncios). Al eliminar la App se borran los ajustes y el progreso almacenados en tu dispositivo."),
 "You can turn usage analytics off in the App under Settings &rarr; Analytics. You can reset": (
  "Você pode desativar a análise de uso no App, em Ajustes &rarr; Análises. Você pode apagar os recordes armazenados localmente na tela de Recordes. Você pode alterar sua escolha de rastreamento de anúncios a qualquer momento (iOS: Ajustes &rarr; Privacidade e Segurança &rarr; Rastreamento). Você pode limitar a personalização de anúncios nas configurações do dispositivo (iOS: Ajustes &rarr; Privacidade e Segurança &rarr; Publicidade da Apple; Android: Configurações &rarr; Google &rarr; Anúncios).",
  "Puedes desactivar las analíticas de uso en la App, en Ajustes &rarr; Analíticas. Puedes borrar los récords almacenados localmente desde la pantalla de Récords. Puedes cambiar tu elección de seguimiento de anuncios en cualquier momento (iOS: Configuración &rarr; Privacidad y seguridad &rarr; Rastreo). Puedes limitar la personalización de anuncios desde los ajustes del dispositivo (iOS: Configuración &rarr; Privacidad y seguridad &rarr; Publicidad de Apple; Android: Configuración &rarr; Google &rarr; Anuncios)."),
 "You can change your ad tracking choice at any time": (
  "Você pode alterar sua escolha de rastreamento de anúncios a qualquer momento (iOS: Ajustes &rarr; Privacidade e Segurança &rarr; Rastreamento). Você pode limitar a personalização de anúncios nas configurações do dispositivo (iOS: Ajustes &rarr; Privacidade e Segurança &rarr; Publicidade da Apple; Android: Configurações &rarr; Google &rarr; Anúncios). Excluir o App remove as configurações e o progresso armazenados no seu dispositivo.",
  "Puedes cambiar tu elección de seguimiento de anuncios en cualquier momento (iOS: Configuración &rarr; Privacidad y seguridad &rarr; Rastreo). Puedes limitar la personalización de anuncios desde los ajustes del dispositivo (iOS: Configuración &rarr; Privacidad y seguridad &rarr; Publicidad de Apple; Android: Configuración &rarr; Google &rarr; Anuncios). Al eliminar la App se borran los ajustes y el progreso almacenados en tu dispositivo."),
 "Changes": ("Alterações", "Cambios"),
 "We may update this policy from time to time.": (
  "Podemos atualizar esta política de tempos em tempos. As alterações relevantes serão refletidas na atualização da data de &ldquo;Última atualização&rdquo; acima.",
  "Podemos actualizar esta política de vez en cuando. Los cambios importantes se reflejarán actualizando la fecha de &ldquo;Última actualización&rdquo; de arriba."),
 "Contact": ("Contato", "Contacto"),
 "Questions about this policy:": (
  "Dúvidas sobre esta política: <a href=\"mailto:contact@solevia.app\">contact@solevia.app</a>",
  "Preguntas sobre esta política: <a href=\"mailto:contact@solevia.app\">contact@solevia.app</a>"),

 # ---- terms
 "These Terms govern your use of {G}": (
  "Estes Termos regem o seu uso do {G} (&ldquo;o App&rdquo;). Ao instalar ou usar o App, você concorda com estes Termos. Se não concordar, não use o App.",
  "Estos Términos rigen tu uso de {G} (&ldquo;la App&rdquo;). Al instalar o usar la App, aceptas estos Términos. Si no estás de acuerdo, no uses la App."),
 "License": ("Licença", "Licencia"),
 "Sole Via Entertainment LLC grants you": (
  "A Sole Via Entertainment LLC concede a você uma licença pessoal, não exclusiva, intransferível e revogável para instalar e usar o App em dispositivos que você possui ou controla, para seu entretenimento pessoal e não comercial.",
  "Sole Via Entertainment LLC te otorga una licencia personal, no exclusiva, intransferible y revocable para instalar y usar la App en dispositivos que poseas o controles, para tu disfrute personal y no comercial."),
 "In-app currency (&ldquo;Glow&rdquo;)": ("Moeda do app (&ldquo;Glow&rdquo;)", "Moneda de la app (&ldquo;Glow&rdquo;)"),
 "In-app currency (&ldquo;Fluff&rdquo;)": ("Moeda do app (&ldquo;Fluff&rdquo;)", "Moneda de la app (&ldquo;Fluff&rdquo;)"),
 "Glow is a soft, in-app currency": (
  "Glow é uma moeda virtual do app, ganha jogando. O Glow não tem valor monetário no mundo real, não pode ser trocado por dinheiro e nunca é vendido por dinheiro de verdade. As skins e os fundos desbloqueados com Glow são cosméticos, só podem ser usados dentro do App e nunca mudam a forma como uma fase é jogada.",
  "Glow es una moneda virtual de la app, que se gana jugando. Glow no tiene valor monetario en el mundo real, no se puede canjear por dinero y nunca se vende por dinero real. Los estilos y fondos que se desbloquean con Glow son cosméticos, solo se pueden usar dentro de la App y nunca cambian cómo se juega un nivel."),
 "Fluff is a soft, in-app currency": (
  "Fluff é uma moeda virtual do app, ganha jogando. O Fluff não tem valor monetário no mundo real, não pode ser trocado por dinheiro e nunca é vendido por dinheiro de verdade. As skins cosméticas e os temas de pote comprados com Fluff só podem ser usados dentro do App e nunca mudam a forma como uma fase é jogada.",
  "Fluff es una moneda virtual de la app, que se gana jugando. Fluff no tiene valor monetario en el mundo real, no se puede canjear por dinero y nunca se vende por dinero real. Los estilos cosméticos y los temas de frasco que se compran con Fluff solo se pueden usar dentro de la App y nunca cambian cómo se juega un nivel."),
 "Rewarded ads": ("Anúncios com recompensa", "Anuncios con recompensa"),
 "Some optional benefits (&ldquo;next move&rdquo;": (
  "Alguns benefícios opcionais (&ldquo;próximo movimento&rdquo;, &ldquo;desfazer um elo&rdquo;, &ldquo;Glow em dobro&rdquo;) são oferecidos em troca de assistir a um anúncio em vídeo com recompensa. Eles são sempre opcionais &mdash; todas as fases do App podem ser concluídas sem assistir a nenhum anúncio.",
  "Algunos beneficios opcionales (&ldquo;siguiente movimiento&rdquo;, &ldquo;desvincular uno&rdquo;, &ldquo;Glow doble&rdquo;) se ofrecen a cambio de ver un anuncio de video con recompensa. Son siempre opcionales &mdash; todos los niveles de la App se pueden completar sin ver ningún anuncio."),
 "Some optional benefits (&ldquo;extra jar&rdquo;": (
  "Alguns benefícios opcionais (&ldquo;pote extra&rdquo;, &ldquo;desfazer&rdquo;) são oferecidos em troca de assistir a um anúncio em vídeo com recompensa. Eles são sempre opcionais &mdash; todas as fases do App podem ser concluídas sem assistir a nenhum anúncio.",
  "Algunos beneficios opcionales (&ldquo;frasco extra&rdquo;, &ldquo;deshacer&rdquo;) se ofrecen a cambio de ver un anuncio de video con recompensa. Son siempre opcionales &mdash; todos los niveles de la App se pueden completar sin ver ningún anuncio."),
 "Acceptable use": ("Uso aceitável", "Uso aceptable"),
 "You agree not to reverse engineer": (
  "Você concorda em não fazer engenharia reversa, modificar ou redistribuir o App, nem tentar interferir no seu funcionamento normal, na sua publicidade ou na sua segurança.",
  "Aceptas no realizar ingeniería inversa, modificar ni redistribuir la App, ni intentar interferir con su funcionamiento normal, su publicidad o su seguridad."),
 "Analytics": ("Análise de uso", "Analíticas"),
 "The App reports anonymous, aggregated usage statistics through Google Analytics for Firebase so we can see how the game is played and fix what is not working. No account, name, or email is involved, and you can switch it off in the App under Settings &rarr; Usage Analytics.": (
  "O App envia estatísticas de uso anônimas e agregadas por meio do Google Analytics para Firebase, para vermos como o jogo é jogado e corrigirmos o que não está funcionando. Nenhuma conta, nome ou e-mail está envolvido, e você pode desativar isso no App, em Ajustes &rarr; Análise de uso. Veja a <a href=\"{PRIV}\">Política de Privacidade</a> para mais detalhes.",
  "La App envía estadísticas de uso anónimas y agregadas mediante Google Analytics para Firebase, para ver cómo se juega y corregir lo que no funciona. No interviene ninguna cuenta, nombre ni correo electrónico, y puedes desactivarlo en la App, en Ajustes &rarr; Analíticas de uso. Consulta la <a href=\"{PRIV}\">Política de Privacidad</a> para más detalles."),
 "The App reports anonymous, aggregated usage statistics through Google Analytics for Firebase so we can see how the game is played and fix what is not working. No account, name, or email is involved, and you can switch it off in the App under Settings &rarr; Analytics.": (
  "O App envia estatísticas de uso anônimas e agregadas por meio do Google Analytics para Firebase, para vermos como o jogo é jogado e corrigirmos o que não está funcionando. Nenhuma conta, nome ou e-mail está envolvido, e você pode desativar isso no App, em Ajustes &rarr; Análises. Veja a <a href=\"{PRIV}\">Política de Privacidade</a> para mais detalhes.",
  "La App envía estadísticas de uso anónimas y agregadas mediante Google Analytics para Firebase, para ver cómo se juega y corregir lo que no funciona. No interviene ninguna cuenta, nombre ni correo electrónico, y puedes desactivarlo en la App, en Ajustes &rarr; Analíticas. Consulta la <a href=\"{PRIV}\">Política de Privacidad</a> para más detalles."),
 "The App reports anonymous, aggregated usage statistics through Google Analytics for Firebase so we can see how the game is played and fix what is not working. No account, name, or email is involved. See": (
  "O App envia estatísticas de uso anônimas e agregadas por meio do Google Analytics para Firebase, para vermos como o jogo é jogado e corrigirmos o que não está funcionando. Nenhuma conta, nome ou e-mail está envolvido. Veja a <a href=\"{PRIV}\">Política de Privacidade</a> para mais detalhes.",
  "La App envía estadísticas de uso anónimas y agregadas mediante Google Analytics para Firebase, para ver cómo se juega y corregir lo que no funciona. No interviene ninguna cuenta, nombre ni correo electrónico. Consulta la <a href=\"{PRIV}\">Política de Privacidad</a> para más detalles."),
 "The App is free and supported by advertising": (
  "O App é gratuito e mantido por publicidade veiculada pelo Google AdMob. Os anunciantes são terceiros e não nos responsabilizamos pelo conteúdo dos anúncios nem dos sites para os quais eles direcionam. Podemos adicionar ou alterar os locais de anúncios ao longo do tempo.",
  "La App es gratuita y se financia con publicidad servida mediante Google AdMob. Los anunciantes son terceros y no somos responsables del contenido de sus anuncios ni de los sitios a los que enlazan. Podemos agregar o cambiar los espacios publicitarios con el tiempo."),
 "No medical claims": ("Sem alegações médicas", "Sin afirmaciones médicas"),
 "The App is intended for entertainment and relaxation.": (
  "O App é destinado ao entretenimento e ao relaxamento. Não é um dispositivo médico e não oferece aconselhamento médico, psicológico ou terapêutico. Se você precisar de ajuda profissional, procure um profissional qualificado.",
  "La App está pensada para el entretenimiento y la relajación. No es un dispositivo médico y no ofrece asesoramiento médico, psicológico ni terapéutico. Si necesitas ayuda profesional, consulta a un profesional calificado."),
 "Disclaimer of warranties": ("Isenção de garantias", "Exención de garantías"),
 "THE APP IS PROVIDED": (
  "O APP É FORNECIDO &ldquo;NO ESTADO EM QUE SE ENCONTRA&rdquo; E &ldquo;CONFORME A DISPONIBILIDADE&rdquo;, SEM GARANTIAS DE QUALQUER TIPO, EXPRESSAS OU IMPLÍCITAS, INCLUINDO GARANTIAS DE COMERCIALIZAÇÃO, ADEQUAÇÃO A UMA FINALIDADE ESPECÍFICA E NÃO VIOLAÇÃO, NA MÁXIMA EXTENSÃO PERMITIDA POR LEI.",
  "LA APP SE PROPORCIONA &ldquo;TAL CUAL&rdquo; Y &ldquo;SEGÚN DISPONIBILIDAD&rdquo;, SIN GARANTÍAS DE NINGÚN TIPO, EXPRESAS O IMPLÍCITAS, INCLUIDAS LAS GARANTÍAS DE COMERCIABILIDAD, IDONEIDAD PARA UN FIN PARTICULAR Y NO INFRACCIÓN, EN LA MÁXIMA MEDIDA PERMITIDA POR LA LEY."),
 "Limitation of liability": ("Limitação de responsabilidade", "Limitación de responsabilidad"),
 "To the maximum extent permitted by law": (
  "Na máxima extensão permitida por lei, a Sole Via Entertainment LLC se isenta de responsabilidade por danos indiretos, incidentais, especiais, consequenciais ou punitivos decorrentes do seu uso do App.",
  "En la máxima medida permitida por la ley, Sole Via Entertainment LLC no se hace responsable de daños indirectos, incidentales, especiales, consecuentes o punitivos derivados de tu uso de la App."),
 "Apple App Store additional terms": ("Termos adicionais da Apple App Store", "Términos adicionales de la Apple App Store"),
 "If you obtained the App from the Apple App Store": (
  "Se você obteve o App na Apple App Store, estes Termos existem somente entre você e a Sole Via Entertainment LLC, e não com a Apple. A Apple e suas subsidiárias são beneficiárias terceiras e podem fazer valer estes Termos.",
  "Si obtuviste la App en la Apple App Store, estos Términos existen únicamente entre tú y Sole Via Entertainment LLC, no con Apple. Apple y sus subsidiarias son terceros beneficiarios y pueden hacerlos valer."),
 "Governing law": ("Lei aplicável", "Ley aplicable"),
 "These Terms are governed by the laws of Florida": (
  "Estes Termos são regidos pelas leis da Flórida, EUA, sem considerar suas regras de conflito de leis.",
  "Estos Términos se rigen por las leyes de Florida, EE. UU., sin tener en cuenta sus normas sobre conflicto de leyes."),
 "These Terms may be updated.": (
  "Estes Termos podem ser atualizados. O uso continuado após as alterações constitui aceitação da versão atualizada.",
  "Estos Términos pueden actualizarse. Seguir usando la App después de los cambios constituye la aceptación de la versión actualizada."),
 "Questions about these Terms:": (
  "Dúvidas sobre estes Termos: <a href=\"mailto:contact@solevia.app\">contact@solevia.app</a>",
  "Preguntas sobre estos Términos: <a href=\"mailto:contact@solevia.app\">contact@solevia.app</a>"),
}
FOOTER = {"pt": "© 2026 Sole Via Entertainment LLC · <a href=\"/pt/\">solevia.app</a>",
          "es": "© 2026 Sole Via Entertainment LLC · <a href=\"/es/\">solevia.app</a>"}
HOME = {"pt": "/pt/", "es": "/es/"}
DAILY = {  # which "Daily ..." feature a game's analytics sentence refers to
    "ring-haven": ("o Anel do Dia", "el Anillo Diario"),
    "squish-sort": ("o Desafio Diário", "el Desafío Diario"),
}

BLOCK = re.compile(r'<(h1|h2|p|li)([^>]*)>(.*?)</\1>|<div class="updated">(.*?)</div>', re.S)


def lookup(text, game, idx):
    """Longest-prefix match of an English block against TR. Returns the translation."""
    norm = text.replace(game, "{G}")
    best = None
    for k, v in TR.items():
        if norm.startswith(k) and (best is None or len(k) > len(best[0])):
            best = (k, v)
    if best is None:
        raise SystemExit(f"no translation for English block: {text[:90]!r}")
    return best[1][idx]


def build_page(src, slug, kind, lang):
    idx = 0 if lang == "pt" else 1
    game = GAMES[slug]
    s = src
    s = s.replace('<html lang="en">', f'<html lang="{LANGS[lang][0]}">', 1)
    priv = f"/{lang}/privacy/{slug}/"

    def sub(m):
        if m.group(1):
            tag, attrs, text = m.group(1), m.group(2), m.group(3)
        else:
            tag, attrs, text = None, "", m.group(4)
        text = text.strip()
        out = lookup(text, game, idx).replace("{G}", game).replace("{PRIV}", priv)
        d = DAILY.get(slug)
        if d:
            out = out.replace("{DAILY_PT}", d[0]).replace("{DAILY_ES}", d[1])
        if tag is None:
            return f'<div class="updated">{out}</div>'
        return f"<{tag}{attrs}>{out}</{tag}>"

    head, body = s.split('<div class="wrap">', 1)
    body = BLOCK.sub(sub, body)
    # <title>
    t = re.search(r"<title>(.*?) · Sole Via Entertainment</title>", head).group(1)
    head = head.replace(t, lookup(t, game, idx).replace("{G}", game), 1)
    # home link text and footer
    body = body.replace('<a class="home" href="/">← Sole Via Entertainment</a>',
                        f'<a class="home" href="{HOME[lang]}">← Sole Via Entertainment</a>', 1)
    body = re.sub(r"<footer>.*?</footer>", f"<footer>{FOOTER[lang]}</footer>", body, flags=re.S)
    s = head + '<div class="wrap">' + body
    return add_alternates(s, slug, kind, lang)


def alternates_head(slug, kind):
    links = []
    for code, (_, hl, _) in LANGS.items():
        path = f"/{kind}/{slug}/" if code == "en" else f"/{code}/{kind}/{slug}/"
        links.append(f'<link rel="alternate" hreflang="{hl}" href="{BASE}{path}" />')
    links.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}/{kind}/{slug}/" />')
    return "\n".join(links)


def switch_html(slug, kind, current):
    items = []
    for code, (hl, _, label) in LANGS.items():
        path = f"/{kind}/{slug}/" if code == "en" else f"/{code}/{kind}/{slug}/"
        if code == current:
            items.append(f'<span aria-current="true">{label}</span>')
        else:
            items.append(f'<a href="{path}" hreflang="{hl}" lang="{hl}">{label}</a>')
    return '<div class="langs">' + " · ".join(items) + "</div>"


CSS = "  .langs{font-size:.85rem;color:var(--muted);margin:-12px 0 22px;}\n  .langs [aria-current]{color:var(--text);font-weight:600;}\n"


def add_alternates(s, slug, kind, current):
    """Idempotently add hreflang links, switch styles and the language switch."""
    s = re.sub(r'<link rel="alternate" hreflang=[^>]*>\n?', "", s)
    s = re.sub(r'<div class="langs">.*?</div>\n?', "", s, flags=re.S)
    s = s.replace(CSS, "")
    s = s.replace("</title>\n", "</title>\n" + alternates_head(slug, kind) + "\n", 1)
    s = s.replace("  footer{margin-top", CSS + "  footer{margin-top", 1)
    s = re.sub(r'(<a class="home"[^>]*>.*?</a>\n)', lambda m: m.group(1) + "    " + switch_html(slug, kind, current) + "\n", s, count=1)
    return s


def main():
    n = 0
    for slug in GAMES:
        for kind in KINDS:
            p = ROOT / kind / slug / "index.html"
            en = p.read_text(encoding="utf-8")
            en = add_alternates(en, slug, kind, "en")
            p.write_text(en, encoding="utf-8")
            for lang in ("pt", "es"):
                out = ROOT / lang / kind / slug / "index.html"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(build_page(en, slug, kind, lang), encoding="utf-8")
                n += 1
    print(f"wrote {n} pages")


if __name__ == "__main__":
    main()
