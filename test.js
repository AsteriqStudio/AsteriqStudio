// test.js
function calculateTotal(price, tax, discount) {
  let total = price + tax;
  if (discount) {
    total = total - discount;
  }
  return total;
}

function unusedFunction() {
  console.log('This function is never used');
}

const x = 10;
const y = 20;
const z = x + y;
console.log(z);

// Deeply nested code
function processOrder(order) {
  if (order) {
    if (order.items) {
      if (order.items.length > 0) {
        if (order.items[0].price) {
          if (order.items[0].price > 100) {
            console.log('Expensive item');
          }
        }
      }
    }
  }
}
