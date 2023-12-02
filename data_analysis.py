import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import os
from chinese_calendar import is_workday
from matplotlib.font_manager import FontProperties    

st.title("商品阅读模板_数据截至2023.11.21")
st.text("销量TOP")

## 准备到款数据
@st.cache_data  # 加载数据优化
def cache_data():
    product_tb = pd.read_csv(r"货品基础数据.csv",encoding="gbk")
    product_tb["品牌_品类"] = product_tb["品牌"] + product_tb["品类"]
    cat_sale = product_tb[product_tb["品类三级"]=="服装"].groupby(["品牌","品类"])["全渠道近15天销量"].sum().reset_index()
    cat_sellout = cat_sale.groupby("品牌",group_keys=False).apply(lambda x: x.nlargest(10,"全渠道近15天销量"))
    cat_sellout["品牌_品类"] = cat_sellout["品牌"] + cat_sellout["品类"]

    sellout_tb = pd.merge(cat_sellout["品牌_品类"],product_tb,how="inner",on="品牌_品类")
    sellout_tb = sellout_tb.groupby("品牌_品类",group_keys=False).apply(lambda x: x.nlargest(5,"全渠道近15天销量"))
    sellout_tb = sellout_tb.loc[:, ["货品编号", "商品标签","品牌", "品类","品牌_品类","吊牌价","全渠道近15天销量","正品（仓+店）全部库存"]
                 ].sort_values(by=["全渠道近15天销量"],ascending=False).reset_index(drop=True)

    ## 准备到色数据
    product_tb_skc = pd.read_csv("①各渠道销售库存到货数据1121.csv",encoding="gbk")
    product_tb_skc["23年零售数量"] = product_tb_skc["23年零售数量"].fillna(0).astype(int)

    ## 准备近货品15日每日销售数据
    sale_15Day_data = pd.read_csv("15日销售.csv",encoding="gbk")
    sale_15Day_data["核销日期"] = pd.to_datetime(sale_15Day_data["核销日期"])
    sale_15Day_data = sale_15Day_data.sort_values(by=["核销日期"],ascending=True).reset_index()
    return product_tb,sellout_tb,cat_sale,product_tb_skc,sale_15Day_data



## 展示数据
def main():
    product_tb,sellout_tb,cat_sale,product_tb_skc,sale_15Day_data = cache_data()
    st.write(sellout_tb)

    st.header("品类销量占比")

    st.subheader("畅销款")
    cate_data = sellout_tb.groupby("品牌_品类")["全渠道近15天销量"].sum()
    st.line_chart(data=cate_data,y="全渠道近15天销量")



    ## 品牌选项框
    brand_option = ["MCS","SBPOLO","MY","LF","ZOOYORK","HC"]
    selectbox_1 = st.selectbox('品牌', brand_option,key="MCS")

    barh_data = cat_sale[(cat_sale["品牌"]==selectbox_1)
                        &(cat_sale["全渠道近15天销量"]>=0)].sort_values(by="全渠道近15天销量",ascending=True).tail(10)

    # 解决中文乱码
    font_path = "SimSun.ttf"
    font_prop = FontProperties(fname=font_path, size=12)
    fig = plt.figure()
    plt.barh(y=barh_data["品类"],width=barh_data["全渠道近15天销量"],height=0.5)
    plt.yticks(fontsize=10, fontproperties=font_prop)
    plt.xticks(fontsize=10, fontproperties=font_prop)
    plt.title(f"{selectbox_1}各品类近15天销量", fontproperties=font_prop)
    for index, value in enumerate(barh_data["全渠道近15天销量"]):
        plt.text(value, index-0.1, str(value))

    st.pyplot(fig)




    # 品类选择框
    cate_option_text = sellout_tb[sellout_tb["品牌"]==selectbox_1].groupby(
        ["品类"])["全渠道近15天销量"].sum().reset_index().sort_values(by=["全渠道近15天销量"],ascending=False)["品类"]
    selectbox_2 = st.selectbox('品类', cate_option_text)

    # 渠道选择框
    channel_option_text = ["正价","奥莱"]
    selectbox_3 = st.selectbox('商品类型', channel_option_text)

    if selectbox_3 == "正价":
        product_kind = "正价款|全渠道款"
    elif selectbox_3 == "奥莱":
        product_kind = "奥莱款|特供款"

    # 显示筛选正价渠道后的数据
    show_data_1 = sellout_tb[(sellout_tb["品牌"]==selectbox_1)
                           &(sellout_tb["品类"]==selectbox_2)
                           &(sellout_tb["商品标签"].str.contains(product_kind))].reset_index(drop=True)
    st.text("正价|全渠道款近15天销量TOP5")
    st.write(show_data_1)


    # 展示图片
    col_1,col_2,col_3,col_4,col_5= st.columns([1,1,1,1,1])
    # 图片地址
    img_path = "图片/"

    with col_1:
        try:
            obj = list(show_data_1["货品编号"])[0]
            st.text(f"{str(obj)}")

            if len(str(obj)) > 1:
                img_obj = img_path + obj + ".jpg"
                img_obj_2 = img_path + obj+ ".png"

            if os.path.exists(img_obj):
                st.image(img_obj)
            elif os.path.exists(img_obj_2):
                st.image(img_obj_2)
            else:
                st.text("没有图片")

            # 货品信息
            st.text(
                f"""
                货季：{list(product_tb[product_tb["货品编号"]==obj]["季节"])[0]}
                商品标签：{list(product_tb[product_tb["货品编号"]==obj]["商品标签"])[0]}
                到销率：{list(product_tb[product_tb["货品编号"]==obj]["到销率"])[0]}
                商品等级：{list(product_tb[product_tb["货品编号"]==obj]["商品等级"])[0]}
                """
            )

            # 到色信息
            st.table(product_tb_skc[product_tb_skc["货品编号"]==obj].loc[:,
                     ["货品颜色编号","23年零售数量","到货数","正品库存数（仓+店）"]].reset_index(drop=True))

            this_product_id = sale_15Day_data[sale_15Day_data["货品编号"]==obj].reset_index()
            this_product_id = pd.merge(pd.DataFrame({"核销日期":list(sale_15Day_data["核销日期"].unique())})
                                       ,this_product_id,how="left",on="核销日期")
            this_product_id["数量"] = this_product_id["数量"].fillna(0)
            this_product_id["周末"] = this_product_id["核销日期"].apply(
                lambda x: 0 if is_workday(x) else max(this_product_id["数量"]))
            this_product_id["核销日期"] = this_product_id["核销日期"].astype(str)

            fig, ax = plt.subplots(figsize=(10,6))
            ax.plot(this_product_id["核销日期"],this_product_id["数量"],linewidth=2,label='销量',color='green')
            ax.bar(this_product_id["核销日期"],this_product_id["周末"],width=1,color="lavender",label='节假日')
            plt.xticks(rotation=45,fontsize=5)
            plt.title(f"近15日 {obj} 销售曲线", fontproperties=font_prop)

            # 添加数据标签
            for index, value in enumerate(this_product_id["数量"]):
                plt.text(index,value+0.1,int(value),ha='center',va='bottom')
            # 显示图例
            ax.legend()

            # 布局到页面上
            st.pyplot(fig)

        except IndexError:
            st.text("无")

    with col_2:
        try:
            obj = list(show_data_1["货品编号"])[1]
            st.text(f"{str(obj)}")
            if len(str(obj)) > 1:
                img_obj = img_path + str(obj).strip() + ".jpg"
                img_obj_2 = img_path + str(obj).strip()+ ".png"

            if os.path.exists(img_obj):
                st.image(img_obj)
            elif os.path.exists(img_obj_2):
                st.image(img_obj_2)
            else:
                st.text("没有图片")
            st.text(
                f"""
                货季：{list(product_tb[product_tb["货品编号"]==obj]["季节"])[0]}
                商品标签：{list(product_tb[product_tb["货品编号"]==obj]["商品标签"])[0]}
                到销率：{list(product_tb[product_tb["货品编号"]==obj]["到销率"])[0]}
                商品等级：{list(product_tb[product_tb["货品编号"]==obj]["商品等级"])[0]}
                """
            )
        except IndexError:
            st.text("无")

    with col_3:
        try:
            obj = list(show_data_1["货品编号"])[2]
            st.text(f"{str(obj)}")

            if len(str(obj)) > 1:
                img_obj = img_path + obj + ".jpg"
                img_obj_2 = img_path + obj+ ".png"

            if os.path.exists(img_obj):
                st.image(img_obj)
            elif os.path.exists(img_obj_2):
                st.image(img_obj_2)
            else:
                st.text("没有图片")

        except IndexError:
            st.text("无")

    with col_4:
        try:
            obj = list(show_data_1["货品编号"])[3]
            st.text(f"{str(obj)}")

            if len(obj) > 1:
                img_obj = img_path +obj + ".jpg"
                img_obj_2 = img_path + obj+ ".png"

            if os.path.exists(img_obj):
                st.image(img_obj)
            elif os.path.exists(img_obj_2):
                st.image(img_obj_2)
            else:
                st.text("没有图片")

        except IndexError:
            st.text("无")

    with col_5:
        try:
            obj = list(show_data_1["货品编号"])[4]
            st.text(f"{str(obj)}")

            if len(obj) > 1:
                img_obj = img_path + obj + ".jpg"
                img_obj_2 = img_path + obj+ ".png"

            if os.path.exists(img_obj):
                st.image(img_obj)
            elif os.path.exists(img_obj_2):
                st.image(img_obj_2)
            else:
                st.text("没有图片")

        except IndexError:
            st.text("无")


if __name__ == '__main__':
    main()


