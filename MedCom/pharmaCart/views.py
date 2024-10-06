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
        external_api_url = 'https://d202-34-125-241-107.ngrok-free.app/'

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

def upload_image_to_ngrok(request):
    if request.method == 'POST':
        # Check if an image is included in the request
        if 'image' not in request.FILES:
            return JsonResponse({"error": "No image file provided"}, status=400)

        # Read the uploaded image file
        image_file = request.FILES['image'].read()

        # Convert the image to Base64
        image_base64 = base64.b64encode(image_file).decode('utf-8')

        # Prepare the JSON payload with Base64-encoded image
        payload = {
            "image_base64": image_base64
        }

        # Ngrok API URL (replace with the actual URL from your Flask app)
        ngrok_api_url = "https://d202-34-125-241-107.ngrok-free.app/"

        try:
            # Send POST request to the Flask API
            response = requests.post(ngrok_api_url, json=payload)

            # Check for a successful response
            if response.status_code == 200:
                # Extract the medicines from the response JSON
                data = response.json()
                medicines = data.get('medicines', 'No medicines found')
                return JsonResponse({"medicines": medicines}, status=200)
            else:
                return JsonResponse({"error": "Failed to retrieve medicines"}, status=response.status_code)

        except requests.exceptions.RequestException as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Invalid request method"}, status=405)


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

        ngrok_api_url = "https://c1eb-34-125-97-60.ngrok-free.app/upload"

        try:
            # Send POST request to the Flask API with the image file
            response = requests.post(ngrok_api_url, files=files)

            # Check for a successful response
            if response.status_code == 200:
                data = response.json()
                medicines = data.get('medicines', 'No medicines found')
                return JsonResponse({"medicines": medicines}, status=200)
            else:
                return JsonResponse({"error": "Failed to retrieve medicines"}, status=response.status_code)

        except requests.exceptions.RequestException as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    # If not POST method, return an error
    return JsonResponse({"error": "Invalid request method"}, status=405)