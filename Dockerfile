FROM python:3.6

ARG project_dir=/blockchain/

# ADD requirements.txt $project_dir
ADD blockchain.py $project_dir

WORKDIR $project_dir

RUN pip install flask
RUN pip install requests
# RUN pip install -r requirements.txt

CMD ["python", "blockchain.py", "5000"]
