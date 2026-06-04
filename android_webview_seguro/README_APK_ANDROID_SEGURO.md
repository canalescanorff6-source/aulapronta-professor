# AulaPronta Pro — APK Android seguro sem Play Store

Este projeto é um APK WebView seguro. Ele abre somente o link online do AulaPronta Professor.

## O que foi reforçado

- Carrega somente o domínio permitido do seu RunSite.
- Bloqueia `http://`, `file://`, `content://`, `data://` e links estranhos.
- Permite abrir WhatsApp para envio de comprovante.
- Não possui JavaScript Bridge (`addJavascriptInterface` não é usado).
- Desativa acesso a arquivos locais.
- Desativa acesso a conteúdo local.
- Bloqueia conteúdo misto HTTP dentro de página HTTPS.
- Cancela carregamento com erro SSL.
- Safe Browsing ativado.
- Sem permissões perigosas: não pede câmera, microfone, localização nem arquivos.
- `allowBackup=false`.
- Release com minificação/ProGuard habilitado.
- O Admin Center não entra no APK.

## Antes de gerar o APK

Abra:

```txt
app/src/main/java/com/aulapronta/pro/MainActivity.java
```

Troque:

```java
private static final String BASE_URL = "https://SEU-LINK-DO-PROFESSOR.runsite.app";
private static final String ALLOWED_HOST = "SEU-LINK-DO-PROFESSOR.runsite.app";
```

Pelo link real do app do professor no RunSite.

Exemplo:

```java
private static final String BASE_URL = "https://aulapronta-professor.runsite.app";
private static final String ALLOWED_HOST = "aulapronta-professor.runsite.app";
```

Nunca coloque o link do Admin Center neste APK.

## Como gerar APK instalável

1. Abra esta pasta `android_webview_seguro` no Android Studio.
2. Espere o Gradle sincronizar.
3. Vá em **Build > Generate Signed Bundle / APK**.
4. Escolha **APK**.
5. Crie uma chave/keystore nova.
6. Escolha **release**.
7. Gere o APK assinado.

O APK final fica normalmente em:

```txt
app/release/app-release.apk
```

## Instalar no celular sem Play Store

1. Envie o APK para o celular.
2. Toque no arquivo APK.
3. O Android pode pedir para permitir instalação por essa fonte.
4. Permita somente para a fonte que você confia.
5. Instale.

## Importante

Guarde o arquivo `.jks` da assinatura em local seguro. Para atualizar o app no futuro, precisa assinar com a mesma chave.
