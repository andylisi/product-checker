from discord_webhook import DiscordWebhook, DiscordEmbed

def sendNotification(webhook_url, product):
    webhook = DiscordWebhook(url=webhook_url)
    embed = DiscordEmbed(title=f'Product in Stock: {product.alias}', description=product.model, color='563d7c', url=product.url)
    embed.add_embed_field(name="Stock", value="Yes")
    embed.add_embed_field(name="Price", value=f'${product.history[0].price}')

    # add embed object to webhook
    webhook.add_embed(embed)
    webhook.execute()