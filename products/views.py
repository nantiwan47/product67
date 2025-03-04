from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from .models import Product, Cart, CartItem, OrderItem, Order
from .forms import RegisterForm, ProductForm
import plotly.graph_objects as go


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    return render(request, 'registration/login.html')

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def profile(request):
    return render(request, 'profile.html')

@login_required
def edit_profile(request):
    if request.method == "POST":
        user = request.user
        user.username = request.POST.get('username')
        user.email = request.POST.get("email")

        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']

        user.save()
        return redirect("profile")

    return render(request, "edit_profile.html")

def admin_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user and (user.is_superuser or getattr(user, "role", "") == "admin"):
            login(request, user)
            messages.success(request, "เข้าสู่ระบบสำเร็จ!")
            return redirect("admin_dashboard")
        else:
            messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    return render(request, "registration/admin-login.html")

@login_required
def admin_logout(request):
    logout(request)
    return redirect("admin_login")



def home(request):
    # ดึงรายการหมวดหมู่จาก choices
    categories = dict(Product.CATEGORY_CHOICES)  # แปลง tuple เป็น dict
    category_products = {}

    # .items() ใช้สำหรับวนลูปใน dictionary โดยจะคืนค่า (key, value)
    for key, label in categories.items():
        products = Product.objects.filter(category=key).order_by('-created_at')[:10]
        if products.exists():  # ตรวจสอบว่าหมวดหมู่นั้นมีสินค้า
            category_products[key] = {"label": label, "products": products}
    return render(request, 'home.html', {'category_products': category_products})

def search_results(request):
    # รับค่าจาก query parameters
    query = request.GET.get('query', '').strip()
    category = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    page_number = request.GET.get('page', 1)  # ดึงค่าหมายเลขหน้าจาก URL

    products = Product.objects.all()

    # ค้นหาตามคำค้นหาหรือชื่อสินค้า
    if query:
        products = products.filter(name__icontains=query)

    # ค้นหาตามหมวดหมู่
    category_choices = dict(Product.CATEGORY_CHOICES)
    if category in category_choices:
        products = products.filter(category=category)

    # ค้นหาตามราคา
    if min_price:
        products = products.filter(price__gte=min_price)  # กรองราคาต่ำสุด
    if max_price:
        products = products.filter(price__lte=max_price)  # กรองราคาสูงสุด

    # ใช้ Paginator แบ่งหน้า (แสดง 10 รายการต่อหน้า)
    paginator = Paginator(products, 10)
    page_obj = paginator.get_page(page_number)


    return render(request, 'search_results.html', {
        'page_obj': page_obj,
        'query': query,
        'category': category,
        'min_price': min_price,
        'max_price': max_price,
        'categories': Product.CATEGORY_CHOICES   # ส่งหมวดหมู่ทั้งหมดไปยัง template
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # คำนวณยอดขายสินค้าที่มีสถานะเป็น "completed"
    sold_quantity = OrderItem.objects.filter(
        product=product,
        order__status='completed'
    ).aggregate(sold_quantity=Sum('quantity'))['sold_quantity'] or 0


    return render(request, 'product_detail.html', {
        'product': product,
        'sold_quantity': sold_quantity,
    })



@login_required
def cart_detail(request):
    # ดึงตะกร้าของผู้ใช้ ถ้าไม่มีจะสร้างขึ้นใหม่
    cart, created = Cart.objects.get_or_create(user=request.user)

    # ถ้ามีตะกร้า ก็จะดึงรายการสินค้าจาก CartItem
    if cart:
        cart_items = CartItem.objects.filter(cart=cart)
    else:
        cart_items = []

        # คำนวณรวมราคาทั้งหมดในตะกร้า
    total_price = sum(item.quantity * item.product.price for item in cart_items)

    return render(request, 'cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user = request.user
    quantity = int(request.POST.get("quantity", 1))

    # ตรวจสอบปริมาณสินค้าในสต็อก
    if quantity > product.stock:
        messages.error(request, f"จำนวนสินค้าที่คุณเลือกมีมากกว่าในสต็อกที่มี ({product.stock} ชิ้น)")
        return redirect('product_detail', pk=product.id)

    # ดึงหรือสร้างรถเข็นของผู้ใช้้าไม่มีถ้าไม่มี
    cart, created = Cart.objects.get_or_create(user=user)

    # ตรวจสอบว่าสินค้าอยู่ในตระกร้าแล้วหรือไม่
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults = {"quantity": quantity}
    )

    if not created:
        # ถ้าสินค้าอยู่ในตะกร้าแล้ว เพิ่มจำนวนสินค้า
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock:
            messages.error(request, f"ไม่สามารถเพิ่มสินค้านี้ได้ เนื่องจากจำนวนในสต็อกไม่เพียงพอ")
            return redirect('product_detail', pk=product.id)
        cart_item.quantity = new_quantity
        cart_item.save()

    return redirect('cart')

@login_required
def update_cart(request, pk):
    if request.method == "POST":
        # ค้นหา CartItem ตาม ID และตรวจสอบว่าเป็นของผู้ใช้ที่ล็อกอิน
        item = get_object_or_404(CartItem, id=pk, cart__user=request.user)

        # รับค่าการกระทำจาก POST request (เพิ่มหรือลดจำนวน)
        action = request.POST.get("action")

        if action == "increase":
            # ตรวจสอบว่าเพิ่มจำนวนเกิน stock หรือไม่
            if item.quantity < item.product.stock:
                item.quantity += 1
            else:
                # ถ้าต้องการเพิ่มเกิน stock
                messages.warning(request,f"ไม่สามารถเพิ่ม {item.product.name} ได้เนื่องจากจำนวนสินค้าในสต็อกมีแค่ {item.product.stock} ชิ้น")
        elif action == "decrease" and item.quantity > 1:
            item.quantity -= 1

        item.save()

    return redirect('cart')

@login_required
def delete_cart(request, pk):
    if request.method == "POST":
        # ค้นหา CartItem ตาม ID และตรวจสอบว่าเป็นของผู้ใช้ที่ล็อกอิน
        item = get_object_or_404(CartItem, id=pk, cart__user=request.user)
        item.delete()
    return redirect('cart')



@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(cart__user=request.user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    if not cart_items:
        messages.error(request, "ตะกร้าของคุณว่างเปล่า กรุณาเลือกสินค้าก่อน")
        return redirect("home")

    if request.method == "POST":
        pickup_time = request.POST.get("pickup_time")
        payment_method = request.POST.get("payment_method")
        slip_image = request.FILES.get("slip_image") if payment_method == "transfer" else None

        if not pickup_time or not payment_method:
            messages.error(request, "กรุณากรอกข้อมูลให้ครบถ้วน")
            return redirect("checkout")

        # ตรวจสอบว่ามีฟิลด์ `order_date` หรือไม่ ถ้าไม่มีให้ใช้ `created_at`
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            status="preparing",
            payment_method=payment_method,
            slip_image=slip_image,
            pickup_time=pickup_time,
            created_at=now()
        )

        # ลดสต็อกสินค้า
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            item.product.stock -= item.quantity
            item.product.save()

        # ล้างตะกร้าหลังจากทำการสั่งซื้อ
        cart_items.delete()

        messages.success(request, "ทำการสั่งซื้อสำเร็จ! กรุณารอการดำเนินการ")
        return redirect("order_status")

    return render(request, "checkout.html", {
        "cart_items": cart_items,
        "total_price": total_price
    })

@login_required
def order_status_view(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
    else:
        orders = []

    return render(request, "order_status.html", {"orders": orders})



def admin_dashboard(request):
    # คำนวณยอดขายรวม
    total_sales = Order.objects.filter(status='completed').aggregate(Sum('total_price'))['total_price__sum'] or 0
    # คำนวณจำนวนคำสั่งซื้อที่รอดำเนินการ
    pending_orders = Order.objects.filter(status='preparing').count()
    # คำนวณจำนวนลูกค้า
    total_customers = Order.objects.values('user').distinct().count()
    # ดึงสินค้าที่เหลือน้อยกว่า 15 ชิ้น
    low_stock_products = Product.objects.filter(stock__lt=15)
    low_stock_count = low_stock_products.count()  # จำนวนสินค้าที่ใกล้หมด


    # สินค้าขายดี 10 อันดับแรก
    top_products = OrderItem.objects.filter(order__status='completed')\
                    .values('product__name')\
                    .annotate(total_sold=Sum('quantity'))\
                    .order_by('-total_sold')[:10]
    product_names = [item['product__name'] for item in top_products]
    product_sold = [item['total_sold'] for item in top_products]
    top_products_graph = go.Figure(data=[go.Bar(
        x=product_names,
        y=product_sold,
        marker=dict(color='blue')
    )])


    # หมวดหมู่สินค้าที่ขายดีที่สุด
    top_categories = OrderItem.objects.filter(order__status='completed') \
                         .values('product__category') \
                         .annotate(total_sold=Sum('quantity')) \
                         .order_by('-total_sold')[:10]
    category_names = [item['product__category'] for item in top_categories]
    category_sold = [item['total_sold'] for item in top_categories]
    top_categories_graph = go.Figure(data=[go.Bar(
        x=category_names,
        y=category_sold,
        marker=dict(color='red')
    )])

    # วิธีการชำระเงินที่ผู้ใช้ใช้บ่อยที่สุด
    payment_methods = Order.objects.exclude(payment_method=None) \
        .values('payment_method') \
        .annotate(count=Count('payment_method')) \
        .order_by('-count')

    # ตรวจสอบว่าไม่ใช่ค่าที่ว่างเปล่า
    if payment_methods.exists():
        payment_names = [item['payment_method'] for item in payment_methods]
        payment_counts = [item['count'] for item in payment_methods]

        payment_graph = go.Figure(data=[go.Pie(labels=payment_names, values=payment_counts)])
        payment_graph.update_layout(title='วิธีการชำระเงินที่ใช้บ่อยที่สุด')

        payment_graph_html = payment_graph.to_html(full_html=False)
    else:
        payment_graph_html = "<p>ไม่มีข้อมูลการชำระเงิน</p>"

    top_customers = Order.objects.filter(status='completed') \
                        .values('user__username') \
                        .annotate(total_spent=Sum('total_price')) \
                        .order_by('-total_spent')[:10]

    customer_names = [item['user__username'] for item in top_customers]
    customer_spending = [item['total_spent'] for item in top_customers]

    top_customers_graph = go.Figure(data=[go.Bar(
        x=customer_names, y=customer_spending,
        name='ลูกค้า', marker=dict(color='purple')
    )])
    top_customers_graph.update_layout(
        title='ผู้ใช้ที่มียอดสั่งซื้อรวมสูงที่สุด 10 อันดับแรก', xaxis_title='ลูกค้า', yaxis_title='ยอดสั่งซื้อ (บาท)',
        template='plotly'
    )

    # ดึงข้อมูลหมวดหมู่ทั้งหมดจาก Product และนับจำนวนสินค้าที่อยู่ในหมวดหมู่นั้นๆ
    category_counts = Product.objects.values('category') \
        .annotate(count=Count('id'))  # นับจำนวนสินค้าในแต่ละหมวดหมู่

    # แปลงข้อมูลให้อยู่ในรูปของชื่อหมวดหมู่และจำนวนสินค้า
    category_names = [dict(Product.CATEGORY_CHOICES).get(item['category'], item['category']) for item in
                      category_counts]
    category_quantities = [item['count'] for item in category_counts]

    # สร้างกราฟแสดงจำนวนสินค้าตามหมวดหมู่
    category_graph = go.Figure(data=[go.Bar(
        x=category_names,  # ชื่อหมวดหมู่ทั้งหมดที่ดึงจากฐานข้อมูล
        y=category_quantities,  # จำนวนสินค้าในหมวดหมู่ต่างๆ
        name='สินค้าตามหมวดหมู่',
        marker=dict(color='orange')
    )])

    category_graph.update_layout(
        title='จำนวนสินค้าตามหมวดหมู่',
        xaxis_title='หมวดหมู่สินค้า',
        yaxis_title='จำนวนสินค้า',
        template='plotly',
        xaxis=dict(tickangle=45)  # หมุนแกน X เพื่อให้ชื่อหมวดหมู่แสดงได้ชัดเจน
    )


    # ส่งข้อมูลไปยัง template
    return render(request, 'admin/dashboard.html', {
        'total_sales': total_sales,
        'pending_orders': pending_orders,
        'total_customers': total_customers,
        'top_products_graph': top_products_graph.to_html(full_html=False),
        'category_graph': category_graph.to_html(full_html=False),  # ส่งกราฟจำนวนสินค้าตามหมวดหมู่
        'top_categories_graph': top_categories_graph.to_html(full_html=False),
        'payment_graph': payment_graph_html,
        'low_stock_count': low_stock_count,  # ส่งจำนวนสินค้าใกล้หมด
        'top_customers_graph': top_customers_graph.to_html(full_html=False)
    })

def product_list(request):
    products = Product.objects.all()  # ดึงสินค้าทั้งหมดจากฐานข้อมูล
    return render(request, 'admin/product_list.html', {'products': products})

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('product_list')  # เปลี่ยนเป็นชื่อ url ที่ต้องการ
    else:
        form = ProductForm()

    return render(request, 'admin/add_product.html', {'form': form})