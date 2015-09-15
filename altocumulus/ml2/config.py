from oslo.config import cfg

CUMULUS_DRIVER_OPTS = [
    cfg.StrOpt('url',
               help='Base URL for the Altocumulus API'),
]

cfg.CONF.register_opts(CUMULUS_DRIVER_OPTS, 'ml2_cumulus')
