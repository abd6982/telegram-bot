from tmessage.decouple import config


DJANGO_TELEGRAMBOT = {

    'MODE': 'WEBHOOK',  #(Optional [str]) # The default value is WEBHOOK,
                        # otherwise you may use 'POLLING'
                        # NB: if use polling you must provide to run
                        # a management command that starts a worker

    'WEBHOOK_SITE': config('WEBHOOK_SITE'),
    'WEBHOOK_PREFIX': '/callback',  # (Optional[str]) # If this value is specified,
                                    # a prefix is added to webhook url

    #'WEBHOOK_CERTIFICATE':  'cert.pem', # If your site use self-signed
                             #certificate, must be set with location of your public key
                             #certificate.(More info at https://core.telegram.org/bots/self-signed )

    'STRICT_INIT': True,    # If set to True, the server will fail to start if some of the
                            # apps contain telegrambot.py files that cannot be successfully
                            # imported.

    'BOTS': [
        {
           'TOKEN': config('TOKEN'), #Your bot token.
            'GROUP_ID': config('GROUP_ID'),

            # List the types of updates you want your bot to receive.
            # For example, specify ["message", "edited_channel_post", "callback_query"]
            # to only receive updates of these types. See 'telegram.Update'
            # for a complete list of available update types.
            # Specify an empty list to receive all updates regardless of type (default).
            # If not specified, the previous setting will be used.
            # Please note that this parameter doesn't affect updates created
            # before the call to the setWebhook, so unwanted updates may be
            # received for a short period of time. (Optional[list[str]])
            #'ALLOWED_UPDATES': (Optional[list[str]]),

            # If this value is specified, use it as the read timeout from the server (Optional[int|float])
            # 'TIMEOUT': 30,

            # Maximum allowed number of simultaneous HTTPS connections to the webhook for update delivery, 1-100.
            # Defaults to 40. Use lower values to limit the load on your bot's server,
            # and higher values to increase your bot's throughput. (Optional[int])
            #'WEBHOOK_MAX_CONNECTIONS': (Optional[int]),



            # Time to wait between polling updates from Telegram in #seconds. Default is 0.0 (Optional[float])
            # 'POLL_INTERVAL' : 0.0,

            # Whether to clean any pending updates on Telegram servers before actually starting to poll.
            # Default is False. Optional[bool])
            # 'POLL_CLEAN': False,

            # Whether the bootstrapping phase of the `Updater`
            # will retry on failures on the Telegram server.
            # |   < 0 - retry indefinitely
            # |     0 - no retries (default)
            # |   > 0 - retry up to X times
            # 'POLL_BOOTSTRAP_RETRIES':(Optional[int]),

            # Grace time in seconds for receiving the reply from server.
            # Will be added to the `timeout` value and used as the read timeout from
            # server (Default: 2).
            # 'POLL_READ_LATENCY': (Optional[float|int]),

        },
        #Other bots here with same structure.
    ],

}