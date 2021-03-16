//pass props(properties) and can access as arg here
//Can also pass in functions as props
const ProductList = ({products, handleDelete}) => {
    return (
        <div className="product-list">
            {products.map((product) => (
                <div className="product-preview" key={ product.id }>
                    <h2>
                        <span>{ product.model } </span>
                        <span> { product.retailer }</span> 
                        <span> { product.available }</span>
                        <button onClick= {() => handleDelete(product.id)}>Delete</button>
                    </h2>
                </div>
            ))}
        </div>
    );
}

export default ProductList;