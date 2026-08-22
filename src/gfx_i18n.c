#include "gfx_i18n.h"

static gfx_lang_t current_lang = GFX_LANG_EN;

void gfx_i18n_init(gfx_lang_t lang)
{
    current_lang = lang;
}

gfx_lang_t gfx_i18n_lang_get(void)
{
    return current_lang;
}

void gfx_i18n_lang_set(gfx_lang_t lang)
{
    current_lang = lang;
}

const char *gfx_i18n_tr(const char *en, const char *zh)
{
    return (current_lang == GFX_LANG_ZH) ? zh : en;
}
