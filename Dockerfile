FROM public.ecr.aws/l4y8s2u6/python3.9

RUN mkdir /app
COPY . /app
WORKDIR /app
EXPOSE 8089

RUN pip3 install -r requirements.txt
CMD ["python", "-u", "app.py"]