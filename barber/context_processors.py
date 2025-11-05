def cart_item_count(request):
    cart_count=0
    if request.user.is_authenticated:
        cart=request.session.get('cart',{})
        if isinstance(cart,dict):
            cart_count=len(cart)
        
    return {'cart_count':cart_count}
    