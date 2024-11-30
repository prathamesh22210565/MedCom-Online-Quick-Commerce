from django.shortcuts import render
from django.http import JsonResponse
import json
import datetime
from .models import * 
from .utils import cookieCart, cartData, guestOrder
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import requests

def store(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}
	return render(request, 'store/store.html', context)


def cart(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)

def checkout(request):
	data = cartData(request)
	
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/checkout.html', context)

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('Product:', productId)

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()

	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment submitted..', safe=False)

def	prescription(request):
	return render(request, 'store/prescription.html')


@csrf_exempt
@require_http_methods(["POST"])
def upload_image(request):
    try:
        # Extract the JSON payload from the request
        data = json.loads(request.body)

        # Get the base64-encoded image data
        base64_image_data = data.get('image_data')

        if not base64_image_data:
            return JsonResponse({"error": "No image data provided"}, status=400)

        # Send the base64 data to your external API
        external_api_url = 'https://4618-34-74-135-60.ngrok-free.app/ocr'

        # Forward the request to the external API
        response = requests.post(
            external_api_url,
            json={"image_data": base64_image_data},
            headers={'Content-Type': 'application/json'}
        )

        # If the external API returns success, relay the response back
        if response.status_code == 200:
            return JsonResponse({"success": "Image uploaded successfully"}, status=200)
        else:
            # If the external API returns an error
            return JsonResponse({"error": "Failed to upload image"}, status=response.status_code)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def upload_image_to_flask(request):
    if request.method == 'POST':
        # Check if an image is included in the request
        if 'image' not in request.FILES:
            return JsonResponse({"error": "No image file provided"}, status=400)

   
        image_file = request.FILES['image']

   
        files = {'image': image_file}

        ngrok_api_url = "https://dc5e-34-74-135-60.ngrok-free.app/ocr"

        try:
            # Send POST request to the Flask API with the image file
            response = requests.post(ngrok_api_url, files=files)

            # Check for a successful response
            if response.status_code == 200:
                data = response.json()
                # medicines = data.get('medicines', 'No medicines found')
                return JsonResponse({"medicines": data}, status=200)
            else:
                return JsonResponse({"error": "Failed to retrieve medicines"}, status=response.status_code)

        except requests.exceptions.RequestException as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    # If not POST method, return an error
    return JsonResponse({"error": "Invalid request method"}, status=405)


import json

@csrf_exempt
def process_medicines(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body.decode('utf-8'))

            # Extract the medicines data from the JSON
            medicines_text = data.get('text', '')
            
            if not medicines_text:
                return JsonResponse({'error': 'No medicines found in the input data.'}, status=400)

            # Split the text into an array of medicines
            medicines_array = [medicine.strip() for medicine in medicines_text.split(',')]

            # Add medicines to the cart
            if request.user.is_authenticated:
                customer = request.user.customer
                order, created = Order.objects.get_or_create(customer=customer, complete=False)

                for medicine_name in medicines_array:
                    try:
                        product = Product.objects.get(name=medicine_name)
                        orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
                        orderItem.quantity = (orderItem.quantity + 1) if not created else 1
                        orderItem.save()
                    except Product.DoesNotExist:
                        return JsonResponse({'error': f'Medicine "{medicine_name}" not found in the database.'}, status=400)
            else:
                # Handle guest cart update
                cookie_data = cookieCart(request)
                cart = cookie_data.get('cart', {})

                for medicine_name in medicines_array:
                    try:
                        product = Product.objects.get(name=medicine_name)
                        product_id = str(product.id)
                        if product_id in cart:
                            cart[product_id]['quantity'] += 1
                        else:
                            cart[product_id] = {'quantity': 1}
                    except Product.DoesNotExist:
                        return JsonResponse({'error': f'Medicine "{medicine_name}" not found in the database.'}, status=400)

                response = JsonResponse({'message': 'Medicines processed successfully for guest cart.', 'medicines': medicines_array})
                response.set_cookie('cart', json.dumps(cart))
                return response

            return JsonResponse({
                'message': 'Medicines processed successfully.',
                'medicines': medicines_array
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method. Only POST requests are allowed.'}, status=405)