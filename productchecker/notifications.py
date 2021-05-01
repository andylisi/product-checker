"""Contains any notification related functions."""

from discord_webhook import DiscordWebhook, DiscordEmbed

def sendNotification(product, new_history):
    """Send Notification to Discord URL provided by user
    
    When an object was previously not in stock but now is, 
    a notification will be sent to them which states the alias,
    model, stock state, and price.

    Args:
        product: A product object.
        new_history: A productHistory object
    """
    webhook = DiscordWebhook(url=product.user.discord_webhook)
    embed = DiscordEmbed(title=f'Product in Stock: {product.alias}', description=product.model, color='563d7c', url=product.url)
    embed.add_embed_field(name="Stock", value="Yes")
    embed.add_embed_field(name="Price", value=f'${new_history.price}')

    # add embed object to webhook
    webhook.add_embed(embed)
    webhook.execute()